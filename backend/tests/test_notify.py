"""Notifications ntfy (0.4.0-c), avec un faux envoi."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update

from jobbot.api.app import create_app
from jobbot.db.models import Evaluation, LlmCall, Offer, OfferStatus, Setting
from jobbot.notify import service
from jobbot.notify.service import Message
from jobbot.runtime import Runtime
from jobbot.settings import Settings
from jobbot.worker.jobs import execute

from .conftest import make_settings

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[Message]:
    messages: list[Message] = []

    async def fake_send(_settings: Settings, message: Message) -> None:
        messages.append(message)

    monkeypatch.setattr(service, "send", fake_send)
    return messages


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, searches, job_runs, llm_calls CASCADE"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'budget_alert_month'"))
    r = Runtime.create(make_settings(ntfy_topic="sujet-secret", public_url="http://jobbot.local"))
    yield r
    await r.dispose()


async def scored(rt: Runtime, n: int, score: int, status: str = OfferStatus.TO_REVIEW) -> int:
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"o{n}",
            title=f"Offre {n}",
            company="Acme SA",
            location="Lausanne, VD",
            first_seen_at=NOW + timedelta(minutes=n),
            last_seen_at=NOW,
            status=status,
        )
        session.add(offer)
        await session.flush()
        session.add(
            Evaluation(
                offer_id=offer.id,
                filter_passed=True,
                filter_reasons=[],
                criteria_hash="x",
                score=score,
                scored_at=NOW,
            )
        )
        return offer.id


async def test_not_configured(runtime: Runtime, sent: list[Message]) -> None:
    assert (await service.notify_new_scores(runtime)).configured is False
    assert sent == []


async def test_grouped_notification_once_per_offer(rt: Runtime, sent: list[Message]) -> None:
    await scored(rt, 1, 72)
    await scored(rt, 2, 88)
    await scored(rt, 3, 40)
    await scored(rt, 4, 95, status=OfferStatus.FILTERED_OUT)

    result = await service.notify_new_scores(rt)

    assert result.offers == 2
    [message] = sent
    assert message.title == "2 nouvelle(s) offre(s) pour toi (jusqu'à 88/100)"
    assert message.message.splitlines() == [
        "88 · Offre 2 — Acme SA (Lausanne, VD)",
        "72 · Offre 1 — Acme SA (Lausanne, VD)",
    ]
    assert message.priority == 4 and message.click == "http://jobbot.local/offres?tri=score"

    assert (await service.notify_new_scores(rt)).offers == 0
    # Une note basse déjà vue ne ressort pas si le seuil baisse ensuite.
    async with rt.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "notify_score_threshold").values(value=30)
        )
    assert (await service.notify_new_scores(rt)).offers == 0
    async with rt.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "notify_score_threshold").values(value=70)
        )
    assert len(sent) == 1


def test_long_list_is_truncated() -> None:
    settings = make_settings()
    rows = [(90 - i, f"Offre {i}", None, None) for i in range(11)]
    message = service.offers_message(settings, rows)
    lines = message.message.splitlines()
    assert len(lines) == service.MAX_LISTED + 1 and lines[-1] == "… et 3 autre(s)"


async def test_budget_alert_once_per_month(rt: Runtime, sent: list[Message]) -> None:
    async with rt.sessionmaker.begin() as session:
        session.add(
            LlmCall(
                purpose="score",
                model="claude-opus-5",
                cost_usd=Decimal("10"),
                cost_chf=Decimal("8.5"),
            )
        )
    first = await service.notify_new_scores(rt)
    again = await service.notify_new_scores(rt)
    assert first.budget_alert and not again.budget_alert
    assert [m.title for m in sent] == ["Budget de l'IA presque atteint"]
    assert "8.50 CHF dépensés sur 10.00 CHF" in sent[0].message


async def test_send_failure_does_not_fail_scoring(
    rt: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def broken(_settings: Settings, _message: Message) -> None:
        raise httpx.ConnectError("hors ligne")

    monkeypatch.setattr(service, "send", broken)
    await scored(rt, 1, 80)
    assert await execute(rt, "score") is True  # sans clé API : rien à noter, mais pas d'échec


async def test_api_test_notification(rt: Runtime, sent: list[Message], settings: Settings) -> None:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        status = (await api.get("/api/notifications")).json()
        assert status == {"configured": True, "server": "https://ntfy.sh"}
        assert (await api.post("/api/notifications/test")).status_code == 204
    assert sent[0].title == "job-bot : notification de test"
    assert "sujet-secret" not in str(status)


async def test_api_test_notification_errors(
    client: AsyncClient, rt: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert (await client.post("/api/notifications/test")).status_code == 409

    async def refused(_settings: Settings, _message: Message) -> None:
        raise httpx.HTTPStatusError(
            "403", request=httpx.Request("POST", "x"), response=httpx.Response(403)
        )

    monkeypatch.setattr(service, "send", refused)
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        assert (await api.post("/api/notifications/test")).status_code == 502


async def test_real_send_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["json"] = request.read().decode()
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def client_factory(**kwargs: Any) -> httpx.AsyncClient:
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    settings = make_settings(ntfy_topic="sujet", ntfy_url="https://ntfy.example/")
    await service.http_send(settings, Message(title="Télé", message="Genève", click="http://x"))
    assert captured["url"] == "https://ntfy.example"
    payload = json.loads(captured["json"])
    assert payload == {
        "topic": "sujet",
        "title": "Télé",
        "message": "Genève",
        "priority": 3,
        "tags": [],
        "click": "http://x",
    }
