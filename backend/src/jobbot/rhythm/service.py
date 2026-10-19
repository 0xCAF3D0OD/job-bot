"""Le bon rythme (docs/86) : l'objectif ORP réparti par semaine, les jours sans recherche, la
dose du jour. Sans IA : des comptes et des règles simples, écrites ici.

- **L'objectif de la semaine** : ce qui reste de l'objectif du mois, au prorata des jours de
  recherche de la semaine sur ceux qui restent dans le mois. Une semaine en retard reporte le
  manque sur toutes les suivantes, sans tout rattraper d'un coup.
- **Les jours sans recherche** : rien sur le téléphone, sauf les rappels qui ont une date limite.
- **La dose du jour** : les 3 meilleures offres à regarder, pas toute la pile (page Aujourd'hui).
"""

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import Application, Setting
from jobbot.orp.service import load_target

# Lundi = 0 … dimanche = 6 ; par défaut, du lundi au vendredi.
DEFAULT_DAYS = (0, 1, 2, 3, 4)
NotifyMode = Literal["daily", "instant"]
DEFAULT_HOUR = 9


@dataclass(frozen=True)
class Rhythm:
    days: tuple[int, ...]
    mode: NotifyMode
    hour: int


@dataclass(frozen=True)
class WeekDay:
    day: date
    research: bool
    sent: int


@dataclass(frozen=True)
class Week:
    # None sans objectif mensuel.
    target: int | None
    count: int
    days: list[WeekDay]
    research_today: bool


def now() -> datetime:
    """L'heure suisse ; remplacée dans les tests par un mardi fixe."""
    return datetime.now(LOCAL_TZ)


def local_today() -> date:
    return now().date()


async def load(session: AsyncSession) -> Rhythm:
    values = {
        s.key: s.value
        for s in await session.scalars(
            select(Setting).where(
                Setting.key.in_(("rhythm_days", "offers_notify_mode", "offers_notify_hour"))
            )
        )
    }
    raw = values.get("rhythm_days")
    days = (
        tuple(sorted({int(d) for d in raw if 0 <= int(d) <= 6}))
        if isinstance(raw, list) and raw
        else DEFAULT_DAYS
    )
    mode: NotifyMode = "instant" if values.get("offers_notify_mode") == "instant" else "daily"
    hour = values.get("offers_notify_hour")
    return Rhythm(days or DEFAULT_DAYS, mode, int(hour) if hour is not None else DEFAULT_HOUR)


async def is_research_day(session: AsyncSession, day: date | None = None) -> bool:
    return (day or local_today()).weekday() in (await load(session)).days


def _research_days(start: date, end: date, days: tuple[int, ...]) -> int:
    return sum(
        1 for n in range((end - start).days + 1) if (start + timedelta(days=n)).weekday() in days
    )


def week_target(month_target: int, sent_before: int, today: date, days: tuple[int, ...]) -> int:
    """La part de la semaine en cours, pour le mois de `today`.

    `sent_before` : candidatures du mois envoyées avant cette semaine (ou avant le 1er jour du
    mois qui tombe dans cette semaine)."""
    month_start = today.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    month_end = next_month - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    start = max(week_start, month_start)
    end = min(week_start + timedelta(days=6), month_end)
    remaining = max(0, month_target - sent_before)
    left_days = _research_days(start, month_end, days)
    span_days = _research_days(start, end, days)
    if not remaining or not span_days:
        return 0
    return math.ceil(remaining * span_days / left_days)


async def week(session: AsyncSession, today: date) -> Week:
    rhythm = await load(session)
    month = f"{today:%Y-%m}"
    week_start = today - timedelta(days=today.weekday())
    start = max(week_start, today.replace(day=1))
    sent = dict(
        (
            await session.execute(
                select(Application.sent_at, func.count())
                .where(
                    Application.sent_at >= week_start,
                    Application.sent_at <= week_start + timedelta(days=6),
                )
                .group_by(Application.sent_at)
            )
        ).all()
    )
    # Les candidatures du mois ORP envoyées cette semaine (sans celles du mois d'avant).
    count = int(
        await session.scalar(
            select(func.count())
            .select_from(Application)
            .where(Application.orp_month == month, Application.sent_at >= start)
        )
        or 0
    )
    target = await load_target(session)
    goal = None
    if target:
        before = int(
            await session.scalar(
                select(func.count())
                .select_from(Application)
                .where(Application.orp_month == month, Application.sent_at < start)
            )
            or 0
        )
        goal = week_target(target, before, today, rhythm.days)
    days = [
        WeekDay(d, d.weekday() in rhythm.days, int(sent.get(d, 0)))
        for d in (week_start + timedelta(days=n) for n in range(7))
    ]
    return Week(goal, count, days, today.weekday() in rhythm.days)
