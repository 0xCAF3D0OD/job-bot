"""Rappels ntfy des preuves ORP : objectif le 25, remise dès le 1er, veille (docs/09 §5)."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select, text

from jobbot.db.models import Application, Notification, OrpMonth, Setting
from jobbot.notify import service as notify
from jobbot.notify.orp import notify_orp
from jobbot.notify.service import Message
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import make_settings


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[Message]:
    messages: list[Message] = []

    async def fake_send(_settings: Settings, message: Message) -> None:
        messages.append(message)

    monkeypatch.setattr(notify, "send", fake_send)
    return messages


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(ntfy_topic="sujet-test"))
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE applications, orp_months, notifications CASCADE"))
        await conn.execute(
            text("DELETE FROM settings WHERE key IN ('orp_monthly_target', 'orp_due_day')")
        )
    async with runtime.sessionmaker.begin() as session:
        session.add(Setting(key="orp_monthly_target", value=20))
    yield runtime
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM settings WHERE key IN ('orp_monthly_target', 'orp_due_day')")
        )
    await runtime.dispose()


async def add(rt: Runtime, sent_at: date, address: str | None = "Rue 1, 1000 Lausanne") -> None:
    async with rt.sessionmaker.begin() as session:
        session.add(
            Application(
                sent_at=sent_at,
                method="electronique",
                company="Acme SA",
                company_address=address,
                job_title="DevOps",
                orp_month=f"{sent_at:%Y-%m}",
            )
        )


async def test_under_target_from_the_25th(rt: Runtime, sent: list[Message]) -> None:
    for day in (2, 9, 16):
        await add(rt, date(2026, 10, day))
    assert await notify_orp(rt, date(2026, 10, 24)) == 0
    assert await notify_orp(rt, date(2026, 10, 25)) == 1
    assert sent[0].title == "3 / 20 candidatures en octobre"
    assert "Il reste 7 jour(s)" in sent[0].message
    assert await notify_orp(rt, date(2026, 10, 26)) == 0  # une seule fois


async def test_due_then_eve_then_nothing_once_submitted(rt: Runtime, sent: list[Message]) -> None:
    await add(rt, date(2026, 9, 3))
    await add(rt, date(2026, 9, 10), address=None)
    assert await notify_orp(rt, date(2026, 10, 1)) == 1
    assert sent[0].title == "Preuves de septembre à remettre avant le 5 octobre"
    assert sent[0].message.startswith("2 candidature(s), 1 ligne(s) à compléter.")
    assert sent[0].click and sent[0].click.endswith("/candidatures/suivi?mois=2026-09")
    assert await notify_orp(rt, date(2026, 10, 2)) == 0
    assert await notify_orp(rt, date(2026, 10, 4)) == 1
    assert sent[1].title == "Demain : preuves de septembre à remettre" and sent[1].priority == 4
    assert await notify_orp(rt, date(2026, 10, 5)) == 0  # date limite passée

    # Mois de novembre : remis avant la date limite, aucun rappel de veille.
    await add(rt, date(2026, 11, 3))
    assert await notify_orp(rt, date(2026, 12, 1)) == 1
    async with rt.sessionmaker.begin() as session:
        record = await session.get(OrpMonth, "2026-11")
        assert record is not None
        record.submitted_at = datetime(2026, 12, 2, 9, 0, tzinfo=UTC)
    assert await notify_orp(rt, date(2026, 12, 4)) == 0


async def test_due_day_setting_and_no_ntfy(rt: Runtime, sent: list[Message]) -> None:
    async with rt.sessionmaker.begin() as session:
        session.add(Setting(key="orp_due_day", value=10))
    await add(rt, date(2026, 9, 3))
    await notify_orp(rt, date(2026, 10, 1))
    assert sent[0].title.endswith("avant le 10 octobre")

    # Sans ntfy : la veille de la date limite, l'alerte est dans la cloche seulement.
    silent = Runtime.create(make_settings())
    try:
        assert await notify_orp(silent, date(2026, 10, 9)) == 1
    finally:
        await silent.dispose()
    assert len(sent) == 1
    async with rt.sessionmaker() as session:
        links = list(await session.scalars(select(Notification.link).order_by(Notification.id)))
    assert links == ["/candidatures/suivi?mois=2026-09"] * 2
