"""Relancer une candidature (docs/38) : message, modèle sans IA, date de la relance."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import Application, Evaluation, LlmCall, Offer
from jobbot.followups import remind, service
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring
from jobbot.settings import Settings

from .conftest import admin_engine

TRUNCATE = "TRUNCATE offers, applications, llm_calls CASCADE"


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
        # Ton identité saisie par le test ne reste pas pour les suivants.
        await conn.execute(text("DELETE FROM settings WHERE key LIKE 'identity_%'"))


async def add(runtime: Runtime, description: str) -> int:
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint="r1",
            title="DevOps Engineer",
            company="Exemple AG",
            status="applied",
            first_seen_at=now,
            last_seen_at=now,
            description=description,
        )
        session.add(offer)
        await session.flush()
        session.add(
            Evaluation(
                offer_id=offer.id,
                filter_passed=True,
                criteria_hash="x",
                strengths=[{"text": "Kubernetes en production", "chunk_ids": []}],
            )
        )
        application = Application(
            offer_id=offer.id,
            sent_at=date(2026, 9, 12),
            method="electronique",
            company="Exemple AG",
            job_title="DevOps Engineer",
            orp_month="2026-09",
            contact_email="rh@exemple.ch",
        )
        session.add(application)
        await session.flush()
        return application.id


async def test_template_without_ai_signed_and_in_the_offer_language(
    api: AsyncClient, runtime: Runtime
) -> None:
    application_id = await add(
        runtime, "Wir suchen einen DevOps Engineer für die Plattform und die Automatisierung."
    )
    await api.put("/api/identity", json={"name": "Camille Exemple"})
    drafted = (await api.post(f"/api/applications/{application_id}/follow-up/draft")).json()
    assert drafted["ai"] is False and drafted["reason"] == "IA non configurée"
    assert drafted["language"] == "de"
    assert drafted["subject"] == "Nachfrage \u2013 Bewerbung DevOps Engineer"
    assert "am 12. September 2026" in drafted["text"]
    assert drafted["text"].endswith("\n\nCamille Exemple")


async def test_ai_message_never_gets_your_name_and_marks_the_follow_up(
    api: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    application_id = await add(runtime, "Nous cherchons un ingénieur DevOps pour la plateforme.")
    await api.put("/api/identity", json={"name": "Camille Exemple", "phone": "+41 79 000 00 00"})
    calls: list[dict[str, Any]] = []

    class Fake:
        async def score(self, params: dict[str, Any]) -> RawResult:
            calls.append(params)
            return RawResult(
                "« Madame, Monsieur, … »", service.MODEL, Usage(600, 0, 0, 60), "end_turn"
            )

    monkeypatch.setattr(scoring, "make_client", lambda _settings: Fake())
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
    drafted = (await api.post(f"/api/applications/{application_id}/follow-up/draft")).json()
    assert drafted["ai"] is True and drafted["language"] == "fr"
    assert drafted["text"] == "Madame, Monsieur, …\n\nCamille Exemple"
    content = calls[0]["messages"][0]["content"]
    assert "12 septembre 2026" in content and "Kubernetes en production" in content
    assert "Camille" not in content and "+41" not in content and "rh@exemple" not in content
    assert calls[0]["model"] == "claude-haiku-4-5"
    async with runtime.sessionmaker() as session:
        assert list(await session.scalars(select(LlmCall.purpose))) == ["relance"]

    marked = (await api.post(f"/api/applications/{application_id}/follow-up")).json()
    # La date de Zurich, comme le service : de minuit à 2 h, la machine (UTC) a un jour de retard.
    assert marked["status"] == "relancee"
    assert marked["followed_up_at"] == service.local_today().isoformat()


async def test_status_set_by_hand_keeps_the_follow_up_date(
    api: AsyncClient, runtime: Runtime
) -> None:
    application_id = await add(runtime, "Poste DevOps.")
    current = next(
        a for a in (await api.get("/api/applications")).json() if a["id"] == application_id
    )
    body = {k: current[k] for k in ("sent_at", "method", "company", "job_title")}
    updated = await api.put(
        f"/api/applications/{application_id}",
        json={**body, "status": "relancee", "status_at": "2026-09-25"},
    )
    assert updated.json()["followed_up_at"] == "2026-09-25"
    assert timedelta(days=14) == service.NO_ANSWER_AFTER


async def test_follow_up_date_chosen_between_5_and_30_days(
    api: AsyncClient, runtime: Runtime
) -> None:
    """L'étape « Suivre » (docs/124 §G) : le jour choisi remplace les 10 jours."""
    application_id = await add(runtime, "Poste DevOps.")
    url = f"/api/applications/{application_id}/follow-up-date"
    # Envoyée le 12 septembre : le 14 est trop tôt, le 20 octobre trop tard.
    assert (await api.patch(url, json={"follow_up_on": "2026-09-14"})).status_code == 422
    assert (await api.patch(url, json={"follow_up_on": "2026-10-20"})).status_code == 422
    chosen = await api.patch(url, json={"follow_up_on": "2026-09-30"})
    assert chosen.json()["follow_up_on"] == "2026-09-30"
    # La candidature d'une offre, pour l'étape « Suivre ».
    offer_id = chosen.json()["offer_id"]
    found = (await api.get("/api/applications", params={"offer": offer_id})).json()
    assert [a["id"] for a in found] == [application_id]
    assert (await api.get("/api/applications", params={"offer": offer_id + 999})).json() == []
    assert (await api.patch("/api/applications/999999/follow-up-date", json={})).status_code == 404
    # Au jour choisi, pas avant : la règle d'Aujourd'hui, des notifications et de l'assistant.
    async with runtime.sessionmaker() as session:
        due = select(Application.id).where(remind.remind_due(date(2026, 9, 29)))
        assert list(await session.scalars(due)) == []
        due = select(Application.id).where(remind.remind_due(date(2026, 9, 30)))
        assert list(await session.scalars(due)) == [application_id]
    # Vide : de nouveau 10 jours après l'envoi (le 22 septembre).
    cleared = await api.patch(url, json={"follow_up_on": None})
    assert cleared.json()["follow_up_on"] is None
    async with runtime.sessionmaker() as session:
        due = select(Application.id).where(remind.remind_due(date(2026, 9, 22)))
        assert list(await session.scalars(due)) == [application_id]
