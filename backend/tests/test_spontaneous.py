"""Candidatures spontanées (docs/39) : créée sans annonce, jamais notée, ligne ORP habituelle."""

from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.db.models import Offer
from jobbot.filtering.duplicates import group_duplicates
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring
from jobbot.settings import Settings

TRUNCATE = "TRUNCATE offers, applications CASCADE"


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text(TRUNCATE))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.engine.begin() as conn:
        await conn.execute(text(TRUNCATE))


async def test_spontaneous_application(api: AsyncClient, runtime: Runtime) -> None:
    created = await api.post(
        "/api/offers/spontaneous",
        json={
            "company": " Exemple SA ",
            "title": "Ingénieur DevOps",
            "reason": "Leur plateforme cloud m'intéresse ; rencontre au salon.",
            "website": "exemple.ch",
        },
    )
    assert created.status_code == 201
    offer_id = created.json()["id"]
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None
        assert (offer.company, offer.status, offer.company_website) == (
            "Exemple SA",
            "preparing",
            "https://exemple.ch",
        )
        # La lettre et le CV lisent ce texte : « Candidature spontanée » en tête.
        data = scoring.offer_data(offer)
        assert data.text is not None and data.text.startswith("Candidature spontanée")
        assert "Poste visé : Ingénieur DevOps" in data.text and not data.partial
        # Jamais notée, jamais doublon.
        assert offer_id not in {
            o.id for o in await scoring.candidates(session, "h", include_stale_profile=True)
        }
    async with runtime.sessionmaker.begin() as session:
        session.add(
            Offer(
                fingerprint="same",
                title="Ingénieur DevOps",
                company="Exemple SA",
                status="to_review",
                first_seen_at=offer.first_seen_at,
                last_seen_at=offer.first_seen_at,
            )
        )
    async with runtime.sessionmaker.begin() as session:
        await group_duplicates(session)
    async with runtime.sessionmaker() as session:
        assert (await session.get(Offer, offer_id)).duplicate_of is None  # type: ignore[union-attr]

    listed = (await api.get("/api/offers", params={"view": "all"})).json()["items"]
    mine = next(o for o in listed if o["id"] == offer_id)
    assert mine["spontaneous"] is True and mine["doubts"] == []

    # Envoyée : une candidature comme les autres, marquée « spontanée ».
    prefill = (await api.get(f"/api/offers/{offer_id}/application-prefill")).json()
    sent = await api.post(
        "/api/applications", json={**prefill, "sent_at": date.today().isoformat()}
    )
    assert sent.status_code in (200, 201)
    applications = (await api.get("/api/applications")).json()
    assert [a["spontaneous"] for a in applications] == [True]

    bad = await api.post(
        "/api/offers/spontaneous", json={"company": "X", "title": " ", "reason": "r"}
    )
    assert bad.status_code == 422
