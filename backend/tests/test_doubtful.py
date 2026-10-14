"""Offres douteuses (docs/30) : doublons regroupés, signaux « à vérifier », filtre, arnaques."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import Evaluation, Offer, OfferLink, OfferStatus
from jobbot.filtering.service import run_filter
from jobbot.llm.scoring import OUTPUT_SCHEMA, ProfileChunkData, parse_output
from jobbot.runtime import Runtime
from jobbot.settings import Settings

NOW = datetime.now(UTC)


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, criteria CASCADE"))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers CASCADE"))


async def add(
    runtime: Runtime,
    key: str,
    title: str,
    company: str | None,
    *,
    days_ago: int = 0,
    status: str = OfferStatus.TO_REVIEW,
    source: str = "jobup",
    scam: list[dict[str, str]] | None = None,
    **extra: Any,
) -> int:
    seen = NOW - timedelta(days=days_ago)
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=key,
            title=title,
            company=company,
            status=status,
            first_seen_at=seen,
            last_seen_at=NOW,
            seen_since=seen,
            **extra,
        )
        session.add(offer)
        await session.flush()
        session.add(OfferLink(offer_id=offer.id, source=source, url=f"https://x/{key}"))
        session.add(
            Evaluation(
                offer_id=offer.id,
                filter_passed=True,
                criteria_hash="x",
                scam_signals=scam or [],
            )
        )
        return offer.id


async def listing(api: AsyncClient, **params: Any) -> dict[str, Any]:
    response = await api.get("/api/offers", params={"view": "all", **params})
    return {o["title"]: o for o in response.json()["items"]}


async def test_duplicates_grouped_under_the_offer_you_acted_on(
    api: AsyncClient, runtime: Runtime
) -> None:
    old = await add(runtime, "d1", "DevOps Engineer", "Exemple SA", days_ago=40, source="jobup")
    sent = await add(
        runtime,
        "d2",
        "DevOps  engineer",
        "EXEMPLE SA",
        days_ago=2,
        status="applied",
        source="linkedin",
    )
    newest = await add(runtime, "d3", "DevOps Engineer", "Exemple SA", days_ago=1, source="indeed")
    await add(runtime, "d4", "DevOps Engineer", "Autre SA")
    await run_filter(runtime)
    async with runtime.sessionmaker() as session:
        rows = {o.id: o for o in await session.scalars(select(Offer))}
    # La candidature envoyée est gardée ; les autres lui sont rattachées.
    assert rows[sent].duplicate_of is None
    assert rows[old].duplicate_of == sent and rows[newest].duplicate_of == sent
    assert rows[sent].seen_since == rows[old].first_seen_at

    offers = (await api.get("/api/offers", params={"view": "all"})).json()["items"]
    assert [o["company"] for o in offers].count("Exemple SA") == 0  # titre de la gardée
    kept = next(o for o in offers if o["id"] == sent)
    assert sorted(link["source"] for link in kept["links"]) == ["indeed", "jobup", "linkedin"]
    assert len(offers) == 2
    # Annonce vue depuis 40 jours (doublons compris) : permanente.
    assert [d["kind"] for d in kept["doubts"]] == ["permanent"]


async def test_doubt_signals_and_hide_filter(api: AsyncClient, runtime: Runtime) -> None:
    await add(runtime, "s1", "SRE", "Exemple SA")
    await add(runtime, "s2", "Assistant", None)
    await add(runtime, "s3", "Data", "Placement SA", employer_status="agency")
    await add(runtime, "s4", "Vieille", "Ancienne SA", days_ago=45)
    await add(runtime, "s5", "Expirée", "Ancienne SA", days_ago=45, expired_at=NOW)
    await add(
        runtime,
        "s6",
        "Gain facile",
        "Arnaque SA",
        scam=[{"reason": "frais de dossier demandés", "excerpt": "50 CHF pour l'ouverture"}],
    )
    found = await listing(api)
    assert found["SRE"]["doubts"] == []
    assert found["Assistant"]["doubts"][0]["kind"] == "hidden_employer"
    assert "agence" in found["Data"]["doubts"][0]["text"]
    assert found["Vieille"]["doubts"][0]["text"].startswith("Annonce permanente : vue dans les")
    expired = await listing(api, view="expired")
    assert expired["Expirée"]["doubts"] == []  # retirée : plus une annonce permanente
    scam = found["Gain facile"]["doubts"][0]
    assert scam["kind"] == "scam" and scam["excerpt"] == "50 CHF pour l'ouverture"

    hidden = await listing(api, hide_doubtful=True)
    assert sorted(hidden) == ["SRE"]


def test_scam_signals_are_capped_and_cleaned() -> None:
    chunks = [ProfileChunkData(1, "competence", "Linux", "Linux")]
    data = {
        "summary_role": "r",
        "summary_asks": "a",
        "summary_offers": "o",
        "score": 50,
        "strengths": [],
        "gaps": [],
        "keywords_role": [],
        "keywords_asks": [],
        "keywords_offers": [],
        "remote": "onsite",
        "remote_days": None,
        "remote_region": None,
        "remote_from_switzerland": None,
        "scam_signals": [
            {"reason": "  contact   par WhatsApp ", "excerpt": "écrivez au 079…"},
            {"reason": "", "excerpt": "vide"},
            {"reason": "b", "excerpt": ""},
            {"reason": "c", "excerpt": ""},
            {"reason": "d", "excerpt": ""},
        ],
    }
    output = parse_output(json.dumps(data), chunks)
    assert [s.reason for s in output.scam_signals] == ["contact par WhatsApp", "b", "c"]
    assert "scam_signals" in OUTPUT_SCHEMA["required"]
    # Réponse plus ancienne, sans le champ : aucune erreur.
    del data["scam_signals"]
    assert parse_output(json.dumps(data), chunks).scam_signals == []
