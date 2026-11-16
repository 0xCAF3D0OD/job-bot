"""Offres douteuses (docs/30) : doublons regroupés, signaux « à vérifier », filtre, arnaques."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import Application, Evaluation, Offer, OfferLink, OfferStatus
from jobbot.filtering.service import run_filter
from jobbot.llm.scoring import OUTPUT_SCHEMA, ProfileChunkData, parse_output
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import admin_engine

NOW = datetime.now(UTC)


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers, applications, criteria CASCADE"))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers, applications CASCADE"))


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
    kept = await add(
        runtime,
        "d2",
        "DevOps  engineer",
        "EXEMPLE SA",
        days_ago=2,
        status="preparing",
        source="linkedin",
    )
    newest = await add(runtime, "d3", "DevOps Engineer", "Exemple SA", days_ago=1, source="indeed")
    await add(runtime, "d4", "DevOps Engineer", "Autre SA")
    await run_filter(runtime)
    async with runtime.sessionmaker() as session:
        rows = {o.id: o for o in await session.scalars(select(Offer))}
    # L'offre en préparation est gardée ; les autres lui sont rattachées.
    assert rows[kept].duplicate_of is None
    assert rows[old].duplicate_of == kept and rows[newest].duplicate_of == kept
    assert rows[kept].seen_since == rows[old].first_seen_at

    offers = (await api.get("/api/offers", params={"view": "all"})).json()["items"]
    assert [o["company"] for o in offers].count("Exemple SA") == 0  # titre de la gardée
    shown = next(o for o in offers if o["id"] == kept)
    assert sorted(link["source"] for link in shown["links"]) == ["indeed", "jobup", "linkedin"]
    assert len(offers) == 2
    # Annonce vue depuis 40 jours (doublons compris) : permanente.
    assert [d["kind"] for d in shown["doubts"]] == ["permanent"]


async def test_sent_offer_hides_only_its_own_page(api: AsyncClient, runtime: Runtime) -> None:
    """Décision de Kevin du 16.11 : même lien qu'une offre envoyée = doublon sûr, rattaché ;
    même titre chez la même entreprise = doublon probable, visible avec « Déjà postulé le … »."""
    sent = await add(runtime, "s1", "DevOps Engineer", "Exemple SA", days_ago=10, status="applied")
    async with runtime.sessionmaker.begin() as session:
        session.add(
            Application(
                offer_id=sent,
                sent_at=date(2026, 11, 4),
                method="electronique",
                company="Exemple SA",
                job_title="DevOps Engineer",
                orp_month="2026-11",
            )
        )
    # La même annonce, relevée dans une autre alerte avec des paramètres de suivi.
    same_page = await add(runtime, "s2", "DevOps engineer (80-100 %)", "Exemple", days_ago=1)
    async with runtime.sessionmaker.begin() as session:
        session.add(
            OfferLink(offer_id=same_page, source="indeed", url="https://www.x/s1/?utm_source=a")
        )
    # Le même titre, republié sur une autre page : un vrai nouveau poste, peut-être.
    republished = await add(runtime, "s3", "DevOps Engineer", "Exemple Sàrl", days_ago=0)
    other = await add(runtime, "s4", "DevOps Engineer", "Autre SA")
    await run_filter(runtime)
    async with runtime.sessionmaker() as session:
        rows = {o.id: o for o in await session.scalars(select(Offer))}
    assert rows[same_page].duplicate_of == sent
    assert rows[republished].duplicate_of is None

    offers = {o["id"]: o for o in (await listing_by_id(api))}
    assert same_page not in offers
    assert offers[republished]["applied_before"] == "2026-11-04"
    assert offers[other]["applied_before"] is None
    assert offers[sent]["applied_before"] is None


async def listing_by_id(api: AsyncClient) -> list[dict[str, Any]]:
    return list((await api.get("/api/offers", params={"view": "all"})).json()["items"])


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

    # « Masquer les agences de placement » (section 35 du 16.11) : seule l'agence part.
    direct = await listing(api, hide_agencies=True)
    assert "Data" not in direct and {"SRE", "Assistant", "Vieille", "Gain facile"} <= set(direct)


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
