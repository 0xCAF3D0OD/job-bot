"""« Cette note ne me correspond pas » (docs/114)."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import Evaluation, LlmCall, Offer, OfferStatus, ProfileChunk, ScoreCorrection
from jobbot.filtering.service import load_criteria
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime
from jobbot.scoring import corrections
from jobbot.scoring import service as scoring

from .conftest import admin_engine, make_settings

TRUNCATE = "TRUNCATE offers, profile_chunks, criteria, llm_calls CASCADE"
NOW = datetime.now(UTC)


async def _offer(rt: Runtime, title: str, **extra: Any) -> int:
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"test:{title}",
            title=title,
            company="Bois & Fils",
            location="Sion",
            status=OfferStatus.TO_REVIEW,
            first_seen_at=NOW,
            last_seen_at=NOW,
            **extra,
        )
        session.add(offer)
        await session.flush()
        session.add(
            Evaluation(
                offer_id=offer.id,
                filter_passed=True,
                filter_reasons=[],
                criteria_hash="t",
                score=78,
                summary_role="Vendre des meubles en magasin.",
            )
        )
        return offer.id


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings())
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
    await runtime.dispose()


@pytest.fixture
async def api(rt: Runtime) -> AsyncIterator[AsyncClient]:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_proposals(api: AsyncClient, rt: Runtime) -> None:
    sale = await _offer(rt, "Vendeur·se en magasin")
    url = f"/api/offers/{sale}/score-correction/proposal"
    high = (await api.post(url, json={"direction": "high", "reason": "not_my_trade"})).json()
    # Sans IA : le modèle simple, avec le titre de l'offre et le mot de la personne.
    assert high["block"]["kind"] == "redhibitoire" and not high["block"]["by_ai"]
    assert "« Vendeur·se en magasin »" in high["block"]["content"]
    low = (
        await api.post(
            url, json={"direction": "low", "reason": "my_trade", "note": "Je l'ai fait 3 ans."}
        )
    ).json()
    assert low["block"]["kind"] == "preference"
    assert low["block"]["content"].endswith("Je l'ai fait 3 ans.")
    # Une raison qui n'existe pas dans ce sens : refusée.
    bad = await api.post(url, json={"direction": "low", "reason": "sector"})
    assert bad.status_code == 422
    missing = await api.post(
        "/api/offers/999999/score-correction/proposal",
        json={"direction": "high", "reason": "other"},
    )
    assert missing.status_code == 404


async def test_place_rate_contract_become_criteria(api: AsyncClient, rt: Runtime) -> None:
    offer = await _offer(rt, "Stage en marketing (50-60 %)", rate_min=50, rate_max=60)
    proposal = (
        await api.post(
            f"/api/offers/{offer}/score-correction/proposal",
            json={"direction": "high", "reason": "place_rate_contract"},
        )
    ).json()
    assert proposal["block"] is None
    by_key = {c["key"]: c for c in proposal["criteria"]}
    assert by_key["min_rate"]["label"] == "Taux minimum 70 %"
    assert by_key["contract_stage"]["changes"] == {"excluded_types": ["stage"]}
    done = await api.put(
        f"/api/offers/{offer}/score-correction",
        json={
            "direction": "high",
            "reason": "place_rate_contract",
            "criteria": by_key["contract_stage"]["changes"],
        },
    )
    assert done.status_code == 200 and done.json()["chunk_id"] is None
    async with rt.sessionmaker() as session:
        assert [t.value for t in (await load_criteria(session)).excluded_types] == ["stage"]
        # Le filtre est repassé : l'offre est écartée.
        assert (await session.get(Offer, offer)).status == OfferStatus.FILTERED_OUT  # type: ignore[union-attr]


async def test_block_added_once_per_offer(api: AsyncClient, rt: Runtime) -> None:
    sale = await _offer(rt, "Vendeur·se en magasin")
    url = f"/api/offers/{sale}/score-correction"
    assert (await api.get(url)).json() is None
    block = {"kind": "redhibitoire", "title": "Pas de vente", "content": "Pas de vente en magasin."}
    first = (
        await api.put(url, json={"direction": "high", "reason": "not_my_trade", "block": block})
    ).json()
    assert first["chunk_id"] and first["score_before"] == 78
    chunks = (await api.get("/api/profile-chunks")).json()
    assert [(c["title"], c["origin"]) for c in chunks] == [("Pas de vente", "correction")]
    # Une correction par offre : la dernière remplace la précédente.
    await api.put(url, json={"direction": "high", "reason": "other", "note": "Trop loin."})
    async with rt.sessionmaker() as session:
        rows = list(await session.scalars(select(ScoreCorrection)))
    assert [(r.reason, r.note) for r in rows] == [("other", "Trop loin.")]
    shown = (await api.get(url)).json()
    assert shown["reason"] == "other" and shown["score"] == 78
    # Le bloc supprimé dans Profil : la correction reste, sans bloc.
    await api.put(url, json={"direction": "high", "reason": "not_my_trade", "block": block})
    chunk_id = (await api.get(url)).json()["chunk_id"]
    await api.delete(f"/api/profile-chunks/{chunk_id}")
    assert (await api.get(url)).json()["chunk_id"] is None


class FakeClient:
    async def score(self, params: dict[str, Any]) -> RawResult:
        answer = {"title": "Pas de vente en magasin", "content": "Je ne cherche pas la vente."}
        return RawResult(
            f"<reponse>{json.dumps(answer)}</reponse>",
            "claude-haiku-4-5",
            Usage(300, 0, 0, 40),
            "end_turn",
        )


async def test_ai_drafts_the_block_then_the_offer_is_rescored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = Runtime.create(make_settings(anthropic_api_key="sk-test"))
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
    monkeypatch.setattr(scoring, "make_client", lambda _settings: FakeClient())
    rescored: list[int] = []

    async def score_offer(_runtime: Runtime, offer_id: int) -> int:
        rescored.append(offer_id)
        return 32

    monkeypatch.setattr(scoring, "score_offer", score_offer)
    try:
        sale = await _offer(runtime, "Vendeur·se en magasin")
        proposal = await corrections.propose(runtime, sale, "high", "not_my_trade", None)
        assert proposal.block is not None and proposal.block.by_ai
        assert proposal.block.title == "Pas de vente en magasin"
        done = await corrections.apply(
            runtime, sale, "high", "not_my_trade", None, proposal.block, None
        )
        assert done.score == 32 and rescored == [sale]
        async with runtime.sessionmaker() as session:
            assert list(await session.scalars(select(LlmCall.purpose))) == ["correction"]
            chunk = await session.get(ProfileChunk, done.chunk_id)
            assert chunk is not None and chunk.origin == "correction" and chunk.active
    finally:
        async with admin_engine().begin() as conn:
            await conn.execute(text(TRUNCATE))
        await runtime.dispose()
