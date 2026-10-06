"""Rappels ntfy des preuves ORP (docs/09-export-orp.md §5).

- le 25 du mois, si les candidatures sont sous l'objectif ;
- le 1er du mois suivant, puis la veille de la date limite si le mois n'est pas remis.

Chaque rappel n'est envoyé qu'une fois par mois (orp_months.reminders_sent) : dans la cloche,
et sur le téléphone si ntfy est configuré.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy.dialects.postgresql import insert

from jobbot.core.orp import LOCAL_TZ, due_date, shift_month
from jobbot.db.models import OrpMonth
from jobbot.log import get_logger
from jobbot.notify import service as notify
from jobbot.orp.service import load_due_day, load_target, month_counts
from jobbot.runtime import Runtime

log = get_logger(__name__)

UNDER_TARGET_DAY = 25
MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]  # fmt: skip


def month_name(month: str) -> str:
    return MONTHS[int(month[5:7]) - 1]


def _long(day: date) -> str:
    return f"{'1er' if day.day == 1 else day.day} {MONTHS[day.month - 1]}"


def _last_day(month: str) -> date:
    year, number = (int(x) for x in shift_month(month, 1).split("-"))
    return date(year, number, 1) - timedelta(days=1)


async def _mark(runtime: Runtime, month: str, sent: dict[str, Any], key: str, day: date) -> None:
    value = {**sent, key: day.isoformat()}
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            insert(OrpMonth)
            .values(month=month, reminders_sent=value)
            .on_conflict_do_update(index_elements=["month"], set_={"reminders_sent": value})
        )


async def notify_orp(runtime: Runtime, today: date | None = None) -> int:
    """Envoie les rappels ORP dus aujourd'hui ; renvoie le nombre de notifications."""
    settings = runtime.settings
    today = today or datetime.now(UTC).astimezone(LOCAL_TZ).date()
    current = f"{today:%Y-%m}"
    previous = shift_month(current, -1)
    base = settings.public_url.rstrip("/")
    sent_count = 0

    async with runtime.sessionmaker() as session:
        due_day = await load_due_day(session)
        target = await load_target(session)
        now_counts = await month_counts(session, current)
        prev_counts = await month_counts(session, previous)
        current_record = await session.get(OrpMonth, current)
        previous_record = await session.get(OrpMonth, previous)

    # 1. Sous l'objectif, à partir du 25.
    current_sent = dict(current_record.reminders_sent or {}) if current_record else {}
    if (
        target
        and today.day >= UNDER_TARGET_DAY
        and now_counts.count < target
        and "under_target" not in current_sent
        and not (current_record and current_record.submitted_at)
    ):
        days_left = (_last_day(current) - today).days + 1
        await notify.deliver(
            runtime,
            notify.Message(
                title=f"{now_counts.count} / {target} candidatures en {month_name(current)}",
                message=f"Il reste {days_left} jour(s) pour atteindre l'objectif.",
                tags=["dart"],
                click=f"{base}/offres",
            ),
            kind="orp_target",
            link="/offres",
        )
        await _mark(runtime, current, current_sent, "under_target", today)
        sent_count += 1

    # 2. Remise du mois précédent : dès le 1er, puis la veille de la date limite.
    deadline = due_date(previous, due_day)
    previous_sent = dict(previous_record.reminders_sent or {}) if previous_record else {}
    submitted = bool(previous_record and previous_record.submitted_at)
    if not submitted and today < deadline:
        key = "eve" if today == deadline - timedelta(days=1) else "due"
        if key not in previous_sent and (key == "eve" or "eve" not in previous_sent):
            details = f"{prev_counts.count} candidature(s)"
            if prev_counts.incomplete:
                details += f", {prev_counts.incomplete} ligne(s) à compléter"
            title = (
                f"Demain : preuves de {month_name(previous)} à remettre"
                if key == "eve"
                else f"Preuves de {month_name(previous)} à remettre avant le {_long(deadline)}"
            )
            await notify.deliver(
                runtime,
                notify.Message(
                    title=title,
                    message=details + ". PDF, CSV ou saisie Job-Room depuis la page ORP.",
                    priority=4 if key == "eve" else 3,
                    tags=["calendar"],
                    click=f"{base}/orp?mois={previous}",
                ),
                kind="orp_due",
                link=f"/orp?mois={previous}",
            )
            await _mark(runtime, previous, previous_sent, key, today)
            sent_count += 1

    if sent_count:
        log.info("orp_reminders_sent", count=sent_count)
    return sent_count
