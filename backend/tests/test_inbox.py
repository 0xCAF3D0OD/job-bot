"""Cloche des alertes (docs/15 §1) : API, collecte en échec, nettoyage."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import Notification
from jobbot.mail.imap import MailboxError
from jobbot.notify import inbox
from jobbot.notify import service as notify
from jobbot.runtime import Runtime
from jobbot.settings import Settings


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE notifications"))
    yield runtime


async def test_inbox_api(rt: Runtime, settings: Settings) -> None:
    for n in range(22):
        await notify.deliver(
            rt, notify.Message(title=f"Alerte {n}", message="texte"), kind="offers", link="/offres"
        )
    app = create_app(settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        box = (await api.get("/api/inbox")).json()
        assert box["unread"] == 22 and len(box["items"]) == 20
        assert box["items"][0]["title"] == "Alerte 21"  # la plus récente en haut
        first = box["items"][0]["id"]
        after = (await api.post(f"/api/inbox/{first}/read")).json()
        assert after["unread"] == 21 and after["items"][0]["read_at"] is not None
        assert (await api.post("/api/inbox/read-all")).json()["unread"] == 0
        assert (await api.post("/api/inbox/999999/read")).status_code == 404


async def test_collect_failure_alert_is_throttled_and_safe(rt: Runtime) -> None:
    error = MailboxError("auth", "AUTHENTICATIONFAILED secret-de-test")
    assert await inbox.collect_failed(rt, error) is True
    assert await inbox.collect_failed(rt, error) is False  # pas plus d'une toutes les 6 h
    async with rt.sessionmaker() as session:
        [alert] = (await session.scalars(select(Notification))).all()
    assert alert.kind == "collect_failed" and alert.link == "/reglages/diagnostic"
    assert "secret" not in alert.message and "mot de passe" in alert.message


async def test_purge_old_alerts(rt: Runtime) -> None:
    async with rt.sessionmaker.begin() as session:
        session.add_all(
            [
                Notification(
                    kind="offers",
                    title="vieille",
                    created_at=datetime.now(UTC) - timedelta(days=91),
                ),
                Notification(kind="offers", title="récente"),
            ]
        )
    assert await inbox.purge(rt) == 1
    async with rt.sessionmaker() as session:
        assert list(await session.scalars(select(Notification.title))) == ["récente"]
