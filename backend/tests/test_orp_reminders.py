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

from .conftest import admin_engine, make_settings


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
    async with admin_engine().begin() as conn:
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


async def add(
    rt: Runtime,
    sent_at: date,
    address: str | None = "Rue 1, 1000 Lausanne",
    job_room_at: date | None = None,
) -> None:
    async with rt.sessionmaker.begin() as session:
        session.add(
            Application(
                sent_at=sent_at,
                method="electronique",
                company="Acme SA",
                company_address=address,
                job_title="DevOps",
                orp_month=f"{sent_at:%Y-%m}",
                job_room_at=job_room_at,
            )
        )


async def test_under_target_from_the_25th(rt: Runtime, sent: list[Message]) -> None:
    for day in (2, 9, 16):
        await add(rt, date(2026, 10, day))
    assert await notify_orp(rt, date(2026, 10, 24)) == 0
    assert await notify_orp(rt, date(2026, 10, 25)) == 1
    assert sent[0].title == "3 / 20 candidatures en octobre"
    assert "Il reste 7 jours" in sent[0].message
    assert await notify_orp(rt, date(2026, 10, 26)) == 0  # une seule fois


async def test_due_then_eve_then_nothing_once_submitted(rt: Runtime, sent: list[Message]) -> None:
    await add(rt, date(2026, 9, 3))
    await add(rt, date(2026, 9, 10), address=None)
    assert await notify_orp(rt, date(2026, 10, 1)) == 1
    assert sent[0].title == "Justificatifs de septembre à remettre avant le 5 octobre"
    assert sent[0].message.startswith("2 candidatures, 1 ligne à compléter.")
    assert sent[0].click and sent[0].click.endswith("/candidatures/suivi?mois=2026-09")
    assert await notify_orp(rt, date(2026, 10, 2)) == 0
    assert await notify_orp(rt, date(2026, 10, 4)) == 1
    assert (
        sent[1].title == "Demain : justificatifs de septembre à remettre" and sent[1].priority == 4
    )
    assert await notify_orp(rt, date(2026, 10, 5)) == 0  # date limite passée

    # Mois de novembre : remis avant la date limite, aucun rappel de veille.
    await add(rt, date(2026, 11, 3))
    assert await notify_orp(rt, date(2026, 12, 1)) == 1
    async with rt.sessionmaker.begin() as session:
        record = await session.get(OrpMonth, "2026-11")
        assert record is not None
        record.submitted_at = datetime(2026, 12, 2, 9, 0, tzinfo=UTC)
    assert await notify_orp(rt, date(2026, 12, 4)) == 0


async def test_due_mentions_job_room_only_when_used(rt: Runtime, sent: list[Message]) -> None:
    """Le compte « à déclarer » n'apparaît que si au moins une est déjà déclarée (docs/70 §6)."""
    await add(rt, date(2026, 9, 3))
    await add(rt, date(2026, 9, 10))
    assert await notify_orp(rt, date(2026, 10, 1)) == 1
    # Un chiffre, pas de consigne (§10.9).
    assert sent[0].message == "2 candidatures."

    await add(rt, date(2026, 9, 17), job_room_at=date(2026, 9, 18))
    assert await notify_orp(rt, date(2026, 10, 4)) == 1
    assert sent[1].message.startswith("3 candidatures, 2 à déclarer dans Job-Room.")


async def test_due_day_setting_and_no_ntfy(rt: Runtime, sent: list[Message]) -> None:
    async with rt.sessionmaker.begin() as session:
        session.add(Setting(key="orp_due_day", value=9))
    await add(rt, date(2026, 9, 3))
    await notify_orp(rt, date(2026, 10, 1))
    # Le vendredi 9 octobre 2026 est ouvrable (un samedi 10 serait reporté au lundi 12).
    assert sent[0].title.endswith("avant le 9 octobre")

    # Sans ntfy : la veille de la date limite, l'alerte est dans la cloche seulement.
    silent = Runtime.create(make_settings())
    try:
        assert await notify_orp(silent, date(2026, 10, 8)) == 1
    finally:
        await silent.dispose()
    assert len(sent) == 1
    async with rt.sessionmaker() as session:
        links = list(await session.scalars(select(Notification.link).order_by(Notification.id)))
    assert links == ["/candidatures/suivi?mois=2026-09"] * 2


def test_justificatifs_elision() -> None:
    """« justificatif » à la place de « preuve » (lot 16.4), avec l'élision devant une voyelle."""
    from jobbot.notify.orp import _of

    assert _of("octobre") == "d'octobre"
    assert _of("septembre") == "de septembre"


async def test_deadline_moves_to_working_day_of_home_canton(
    rt: Runtime, sent: list[Message]
) -> None:
    """Le 5 septembre 2024 est le Jeûne genevois : à Genève, l'échéance passe au vendredi 6."""
    async with rt.sessionmaker.begin() as session:
        session.add(Setting(key="identity_postcode", value="1204"))
    await add(rt, date(2024, 8, 12))
    await notify_orp(rt, date(2024, 9, 1))
    assert sent[0].title.endswith("avant le 6 septembre")
