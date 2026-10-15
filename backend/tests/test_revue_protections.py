"""Revue 0.33.1 (docs/41 §3) : la ligne ORP, le plafond de l'IA, l'agenda."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.agenda import service as agenda
from jobbot.api.app import create_app
from jobbot.core.orp import shift_month
from jobbot.db.models import Application, OrpMonth, Setting
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring
from jobbot.settings import Settings

TRUNCATE = "TRUNCATE offers, applications, contacts, llm_calls, orp_months CASCADE"
BUDGET = "llm_monthly_budget_chf"


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text(TRUNCATE))
        budget = await conn.scalar(
            text("SELECT value FROM settings WHERE key = :key"), {"key": BUDGET}
        )
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.engine.begin() as conn:
        await conn.execute(text(TRUNCATE))
        # Le plafond reprend sa valeur : d'autres tests le lisent.
        await conn.execute(text("DELETE FROM settings WHERE key = :key"), {"key": BUDGET})
        if budget is not None:
            await conn.execute(
                text("INSERT INTO settings (key, value) VALUES (:key, CAST(:value AS jsonb))"),
                {"key": BUDGET, "value": json.dumps(budget)},
            )


async def test_spontaneous_orp_line_is_complete(api: AsyncClient) -> None:
    offer_id = (
        await api.post(
            "/api/offers/spontaneous",
            json={"company": "Exemple SA", "title": "Ingénieur DevOps", "reason": "Leur cloud."},
        )
    ).json()["id"]
    prefill = (await api.get(f"/api/offers/{offer_id}/application-prefill")).json()
    today = date.today()
    sent = await api.post(
        "/api/applications",
        json={
            **prefill,
            "sent_at": today.isoformat(),
            "company_address": "Rue du Lac 1\n1000 Lausanne",
        },
    )
    assert sent.status_code in (200, 201)
    month = (await api.get("/api/orp", params={"month": f"{today:%Y-%m}"})).json()
    [row] = month["rows"]
    assert row["missing"] == []
    assert (row["company"], row["job_title"]) == ("Exemple SA", "Ingénieur DevOps")
    assert row["method"] and row["result"]


class Counting:
    calls = 0

    async def score(self, params: dict[str, Any]) -> Any:
        Counting.calls += 1
        raise AssertionError("aucun appel à l'IA au-delà du plafond")


async def test_ai_cap_template_or_refusal_without_a_call(
    api: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(scoring, "make_client", lambda _settings: Counting())
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
    async with runtime.sessionmaker.begin() as session:
        await session.merge(Setting(key=BUDGET, value=0))
        application = Application(
            sent_at=date.today(),
            method="electronique",
            company="Exemple SA",
            job_title="DevOps Engineer",
            orp_month=f"{date.today():%Y-%m}",
        )
        session.add(application)
        await session.flush()
        application_id = application.id
    drafted = (await api.post(f"/api/applications/{application_id}/follow-up/draft")).json()
    assert drafted["ai"] is False and drafted["reason"] == "plafond mensuel de l'IA atteint"
    message = await api.post(
        "/api/contacts/message", json={"application_id": application_id, "role": "team"}
    )
    assert message.status_code == 409 and "plafond" in message.json()["detail"]
    assert Counting.calls == 0


async def test_agenda_skips_a_submitted_orp_month(api: AsyncClient, runtime: Runtime) -> None:
    current = f"{date.today():%Y-%m}"
    previous = shift_month(current, -1)
    async with runtime.sessionmaker.begin() as session:
        for month in (previous, current):
            session.add(
                Application(
                    sent_at=date.fromisoformat(f"{month}-01"),
                    method="electronique",
                    company="Exemple SA",
                    job_title="DevOps Engineer",
                    status="refus",
                    orp_month=month,
                )
            )
        session.add(OrpMonth(month=previous, submitted_at=datetime.now(UTC)))
    async with runtime.sessionmaker() as session:
        uids = [e.uid for e in await agenda.events(session, "https://x")]
    assert f"orp-{current}@joba1" in uids
    assert f"orp-{previous}@joba1" not in uids
