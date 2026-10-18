"""Revue 0.33.1 (docs/41) : chaque correction a son test."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import anthropic
import httpx2
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.agenda import service as agenda
from jobbot.api.app import create_app
from jobbot.db.models import Application, Offer
from jobbot.enrich.service import expire_stale
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring
from jobbot.settings import Settings

from .conftest import admin_engine

TRUNCATE = "TRUNCATE offers, applications, contacts, trainings, llm_calls CASCADE"


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))


async def add_application(runtime: Runtime, **values: Any) -> int:
    today = date.today()
    defaults: dict[str, Any] = {
        "sent_at": today - timedelta(days=12),
        "method": "electronique",
        "company": "Exemple SA",
        "job_title": "DevOps Engineer",
        "orp_month": f"{today:%Y-%m}",
    }
    async with runtime.sessionmaker.begin() as session:
        application = Application(**{**defaults, **values})
        session.add(application)
        await session.flush()
        return application.id


async def test_spontaneous_never_expires_by_age(api: AsyncClient, runtime: Runtime) -> None:
    created = await api.post(
        "/api/offers/spontaneous",
        json={"company": "Exemple SA", "title": "SRE", "reason": "Leur plateforme."},
    )
    offer_id = created.json()["id"]
    later = datetime.now(UTC) + timedelta(days=40)
    await expire_stale(runtime, later)
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None and offer.expired_at is None


class Flaky:
    async def score(self, params: dict[str, Any]) -> Any:
        raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api"))


async def test_transient_ai_errors_fall_back(
    api: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(scoring, "make_client", lambda _settings: Flaky())
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
    application_id = await add_application(runtime)
    drafted = await api.post(f"/api/applications/{application_id}/follow-up/draft")
    assert drafted.status_code == 200
    assert drafted.json()["ai"] is False
    assert drafted.json()["reason"] == "IA momentanément indisponible"
    message = await api.post(
        "/api/contacts/message", json={"application_id": application_id, "role": "team"}
    )
    assert message.status_code == 409 and "réessaie" in message.json()["detail"]


async def test_follow_up_dates_and_statuses(api: AsyncClient, runtime: Runtime) -> None:
    application_id = await add_application(runtime)
    url = f"/api/applications/{application_id}"
    marked = (await api.post(f"{url}/follow-up")).json()
    assert marked["followed_up_at"] == marked["status_at"]
    # Seule une candidature en attente se relance.
    assert (await api.post(f"{url}/follow-up")).status_code == 409
    body = {k: marked[k] for k in ("sent_at", "method", "company", "job_title")}
    back = (await api.put(url, json={**body, "status": "en_attente"})).json()
    assert back["followed_up_at"] is None
    again = (
        await api.put(url, json={**body, "status": "relancee", "status_at": "2026-10-01"})
    ).json()
    assert again["followed_up_at"] == "2026-10-01"


async def test_today_counts_like_the_follow_up_list(api: AsyncClient, runtime: Runtime) -> None:
    today = date.today()
    await add_application(runtime)  # en attente depuis 12 jours
    await add_application(runtime, status="relancee", followed_up_at=today - timedelta(days=15))
    await add_application(runtime, status="relancee", followed_up_at=today - timedelta(days=3))
    assert (await api.get("/api/today")).json()["to_follow_up"] == 2


async def test_contact_attachment_is_checked(api: AsyncClient, runtime: Runtime) -> None:
    contact = {"role": "team", "channel": "email", "contacted_on": date.today().isoformat()}
    assert (
        await api.post("/api/contacts", json={**contact, "offer_id": 999_999})
    ).status_code == 404
    assert (
        await api.post("/api/contacts", json={**contact, "application_id": 999_999})
    ).status_code == 404
    first = (
        await api.post(
            "/api/offers/spontaneous",
            json={"company": "A", "title": "SRE", "reason": "r"},
        )
    ).json()["id"]
    other = (
        await api.post(
            "/api/offers/spontaneous",
            json={"company": "B", "title": "SRE", "reason": "r"},
        )
    ).json()["id"]
    application_id = await add_application(runtime, offer_id=first)
    mismatch = await api.post(
        "/api/contacts",
        json={**contact, "offer_id": other, "application_id": application_id},
    )
    assert mismatch.status_code == 422


async def test_one_profile_block_per_training(api: AsyncClient) -> None:
    training = (await api.get("/api/trainings")).json()["items"][0]
    await api.put(f"/api/trainings/{training['id']}/mark", json={"status": "done"})
    url = f"/api/trainings/{training['id']}/profile-block"
    block = {"title": "Formation", "content": "Terminée.", "tags": []}
    first = await api.post(url, json=block)
    assert first.status_code == 201
    assert (await api.post(url, json=block)).status_code == 409
    async with api._transport.app.state.runtime.engine.begin() as conn:  # type: ignore[attr-defined]
        await conn.execute(
            text("DELETE FROM profile_chunks WHERE id = :id").bindparams(
                id=first.json()["chunk_id"]
            )
        )


async def test_agenda_leaves_out_closed_and_old(runtime: Runtime) -> None:
    today = date.today()
    soon = datetime.now(UTC) + timedelta(days=2)
    await add_application(runtime, company="Ancienne SA", sent_at=today - timedelta(days=45))
    await add_application(runtime, company="Fermée SA", status="refus", interview_at=soon)
    await add_application(runtime, company="Ouverte SA", status="entretien", interview_at=soon)
    async with runtime.sessionmaker() as session:
        titles = [e.summary for e in await agenda.events(session, "https://x")]
    assert "Entretien \u2013 Ouverte SA" in titles
    assert not any("Fermée SA" in t or "Ancienne SA" in t for t in titles)
