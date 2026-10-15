"""Contacts dans l'entreprise (docs/31) : recherches, prises de contact, relance, Aujourd'hui."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.contacts import service
from jobbot.db.models import Application, Notification, Offer, ProfileChunk
from jobbot.runtime import Runtime
from jobbot.settings import Settings


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE offers, applications, contacts, notifications, profile_chunks CASCADE")
        )
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE offers, applications, contacts, notifications, profile_chunks CASCADE")
        )


def keywords(url: str) -> str:
    return parse_qs(urlsplit(url).query)["keywords"][0]


def test_role_words_and_school() -> None:
    assert service.role_words("DevOps Engineer (H/F) 80-100 %") == "DevOps Engineer"
    assert service.role_words("Senior Platform / Cloud Engineer") == "Platform Cloud Engineer"
    assert service.school_of("42 Lausanne (2021 \u2013 2023) et maturité professionnelle") == (
        "42 Lausanne"
    )
    assert service.school_of("EPFL, Master en informatique") == "EPFL"


async def test_searches_contacts_and_follow_up(api: AsyncClient, runtime: Runtime) -> None:
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint="c1",
            title="DevOps Engineer (H/F)",
            company="Exemple SA",
            status="applied",
            first_seen_at=now,
            last_seen_at=now,
            company_website="https://www.exemple.ch",
        )
        session.add(offer)
        session.add(
            ProfileChunk(kind="formation", title="42 Lausanne (2021 \u2013 2023)", content="…")
        )
        await session.flush()
        application = Application(
            offer_id=offer.id,
            sent_at=date.today(),
            method="electronique",
            company="Exemple SA",
            job_title="DevOps Engineer",
            orp_month=f"{date.today():%Y-%m}",
        )
        session.add(application)
        await session.flush()
        offer_id, application_id = offer.id, application.id

    page = (await api.get(f"/api/offers/{offer_id}/contacts")).json()
    assert [s["kind"] for s in page["searches"]] == ["recruiting", "team", "alumni"]
    assert keywords(page["searches"][0]["url"]).startswith("Exemple SA recruiter")
    assert keywords(page["searches"][1]["url"]) == "Exemple SA DevOps Engineer"
    assert keywords(page["searches"][2]["url"]) == "Exemple SA 42 Lausanne"
    assert page["website"] == "https://www.exemple.ch" and page["contacts"] == []

    # Contact ajouté depuis l'offre : rattaché aussi à la candidature.
    old = (date.today() - timedelta(days=8)).isoformat()
    created = (
        await api.post(
            "/api/contacts",
            json={
                "offer_id": offer_id,
                "name": " Marie ",
                "role": "recruiter",
                "channel": "linkedin_invite",
                "contacted_on": old,
            },
        )
    ).json()
    assert created["application_id"] == application_id and created["name"] == "Marie"
    listed = (await api.get("/api/applications")).json()
    assert [c["name"] for c in listed[0]["contacts"]] == ["Marie"]
    assert (await api.get(f"/api/applications/{application_id}/contacts")).json()["contacts"]
    assert (await api.get("/api/today")).json()["contacts_to_follow_up"] == 1

    # Relance une seule fois, sans le nom dans le titre si inconnu.
    assert await service.notify_contacts(runtime) == 1
    assert await service.notify_contacts(runtime) == 0
    async with runtime.sessionmaker() as session:
        [alert] = (await session.scalars(select(Notification))).all()
    assert alert.title == "Relancer Marie chez Exemple SA ?" and alert.kind == "contact_follow_up"

    # « A répondu » : plus rien à relancer.
    answered = await api.put(
        f"/api/contacts/{created['id']}",
        json={**created, "answered_on": date.today().isoformat(), "note": "Appel jeudi"},
    )
    assert answered.json()["note"] == "Appel jeudi"
    assert (await api.get("/api/today")).json()["contacts_to_follow_up"] == 0
    assert (await api.delete(f"/api/contacts/{created['id']}")).status_code == 204
    missing = await api.post(
        "/api/contacts", json={"role": "team", "channel": "email", "contacted_on": old}
    )
    assert missing.status_code == 422
