"""Le bon rythme (docs/86) : l'objectif ORP réparti par semaine, les jours de repos, la
pause, le signal de fin de semaine. Sans IA : des comptes et des règles simples, écrites ici.

- **L'objectif de la semaine** : ce qui reste de l'objectif du mois, au prorata des jours de
  recherche de la semaine sur ceux qui restent dans le mois. Une semaine en retard reporte le
  manque sur toutes les suivantes, sans tout rattraper d'un coup.
- **Les jours de repos** : rien sur le téléphone, sauf les rappels qui ont une date limite.
- **La pause** (0.68.1) : ses jours ne sont pas des jours de recherche, et l'objectif du mois
  est réduit d'autant pour le rythme, sans dette à rattraper. L'objectif ORP, lui, ne change
  pas : c'est le conseiller qui décide.
- **La dose du jour** : les 3 meilleures offres à regarder, pas toute la pile (page Aujourd'hui).
- **Le signal de la semaine** (0.68.1) : un message, le dernier jour de recherche de la semaine,
  à 17 h : à jour, en retard, ou trop d'envois sur des offres peu notées.
"""

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import Application, Evaluation, Offer, OfferStatus, Setting
from jobbot.letters.document import MONTHS
from jobbot.orp.service import load_target

# Lundi = 0 … dimanche = 6 ; par défaut, du lundi au vendredi.
DEFAULT_DAYS = (0, 1, 2, 3, 4)
NotifyMode = Literal["daily", "instant"]
DEFAULT_HOUR = 9
DOSE = 3
# Le signal de la semaine : à 17 h, le dernier jour de recherche.
SIGNAL_HOUR = 17
SIGNAL_KEY = "rhythm_signal_week"
# « Trop » : une fois et demie le rythme (et 2 de plus au moins), avec au moins 2 envois sur
# des offres notées sous 50.
TOO_MUCH = 1.5
LOW_SCORE = 50
LOW_MIN = 2
DAY_NAMES = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
WeekState = Literal["done", "missed", "current", "upcoming", "pause"]


@dataclass(frozen=True)
class Rhythm:
    days: tuple[int, ...]
    mode: NotifyMode = "daily"
    hour: int = DEFAULT_HOUR
    pause_from: date | None = None
    pause_until: date | None = None

    def paused(self, day: date) -> bool:
        return (
            self.pause_from is not None
            and self.pause_until is not None
            and self.pause_from <= day <= self.pause_until
        )

    def research(self, day: date) -> bool:
        return day.weekday() in self.days and not self.paused(day)


@dataclass(frozen=True)
class WeekDay:
    day: date
    research: bool
    sent: int
    paused: bool = False


@dataclass(frozen=True)
class Week:
    # None sans objectif mensuel.
    target: int | None
    count: int
    days: list[WeekDay]
    research_today: bool
    # La fin de la pause en cours, s'il y en a une aujourd'hui.
    pause_until: date | None = None


@dataclass(frozen=True)
class MonthWeek:
    start: date
    end: date
    target: int | None
    count: int
    state: WeekState


@dataclass(frozen=True)
class Signal:
    kind: Literal["done", "late", "too_much"]
    title: str
    message: str


def now() -> datetime:
    """L'heure suisse ; remplacée dans les tests par un mardi fixe."""
    return datetime.now(LOCAL_TZ)


def local_today() -> date:
    return now().date()


def _date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


async def load(session: AsyncSession) -> Rhythm:
    keys = (
        "rhythm_days",
        "offers_notify_mode",
        "offers_notify_hour",
        "rhythm_pause_from",
        "rhythm_pause_until",
    )
    values = {
        s.key: s.value for s in await session.scalars(select(Setting).where(Setting.key.in_(keys)))
    }
    raw = values.get("rhythm_days")
    days = (
        tuple(sorted({int(d) for d in raw if 0 <= int(d) <= 6}))
        if isinstance(raw, list) and raw
        else DEFAULT_DAYS
    )
    mode: NotifyMode = "instant" if values.get("offers_notify_mode") == "instant" else "daily"
    hour = values.get("offers_notify_hour")
    return Rhythm(
        days or DEFAULT_DAYS,
        mode,
        int(hour) if hour is not None else DEFAULT_HOUR,
        _date(values.get("rhythm_pause_from")),
        _date(values.get("rhythm_pause_until")),
    )


async def is_research_day(session: AsyncSession, day: date | None = None) -> bool:
    return (await load(session)).research(day or local_today())


def _research_days(start: date, end: date, rhythm: Rhythm, *, pause: bool = True) -> int:
    count = 0
    for n in range((end - start).days + 1):
        day = start + timedelta(days=n)
        if day.weekday() in rhythm.days and not (pause and rhythm.paused(day)):
            count += 1
    return count


def _month_bounds(day: date) -> tuple[date, date]:
    start = day.replace(day=1)
    return start, (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)


def week_target(month_target: int, sent_before: int, today: date, rhythm: Rhythm) -> int:
    """La part de la semaine en cours, pour le mois de `today`.

    `sent_before` : candidatures du mois envoyées avant cette semaine (ou avant le 1er jour du
    mois qui tombe dans cette semaine). Une pause réduit l'objectif du mois d'autant, pour le
    rythme seulement : pas de dette à rattraper ensuite."""
    month_start, month_end = _month_bounds(today)
    all_days = _research_days(month_start, month_end, rhythm, pause=False)
    open_days = _research_days(month_start, month_end, rhythm)
    goal = math.ceil(month_target * open_days / all_days) if all_days else 0
    week_start = today - timedelta(days=today.weekday())
    start = max(week_start, month_start)
    end = min(week_start + timedelta(days=6), month_end)
    remaining = max(0, goal - sent_before)
    left_days = _research_days(start, month_end, rhythm)
    span_days = _research_days(start, end, rhythm)
    if not remaining or not span_days:
        return 0
    return math.ceil(remaining * span_days / left_days)


async def _count(session: AsyncSession, month: str, start: date, end: date | None = None) -> int:
    query = (
        select(func.count())
        .select_from(Application)
        .where(Application.orp_month == month, Application.sent_at >= start)
    )
    if end is not None:
        query = query.where(Application.sent_at <= end)
    return int(await session.scalar(query) or 0)


async def _before(session: AsyncSession, month: str, start: date) -> int:
    return int(
        await session.scalar(
            select(func.count())
            .select_from(Application)
            .where(Application.orp_month == month, Application.sent_at < start)
        )
        or 0
    )


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
    count = await _count(session, month, start)
    target = await load_target(session)
    goal = None
    if target:
        goal = week_target(target, await _before(session, month, start), today, rhythm)
    days = [
        WeekDay(d, rhythm.research(d), int(sent.get(d, 0)), rhythm.paused(d))
        for d in (week_start + timedelta(days=n) for n in range(7))
    ]
    return Week(
        goal,
        count,
        days,
        rhythm.research(today),
        rhythm.pause_until if rhythm.paused(today) else None,
    )


async def month_weeks(session: AsyncSession, month: str, today: date) -> list[MonthWeek]:
    """Les semaines d'un mois (Bilan) : faites, manquées, en cours, à venir, ou en pause.
    L'objectif de chaque semaine est recalculé avec les réglages d'aujourd'hui."""
    rhythm = await load(session)
    target = await load_target(session)
    year, number = (int(x) for x in month.split("-"))
    month_start, month_end = _month_bounds(date(year, number, 1))
    found: list[MonthWeek] = []
    start = month_start
    while start <= month_end:
        end = min(start + timedelta(days=6 - start.weekday()), month_end)
        count = await _count(session, month, start, end)
        goal = (
            week_target(target, await _before(session, month, start), start, rhythm)
            if target
            else None
        )
        state: WeekState
        working = _research_days(start, end, rhythm, pause=False)
        if start > today:
            state = "upcoming"
        elif working and not _research_days(start, end, rhythm):
            state = "pause"
        elif end >= today:
            state = "current"
        else:
            state = "done" if goal is None or count >= goal else "missed"
        found.append(MonthWeek(start, end, goal, count, state))
        start = end + timedelta(days=1)
    return found


def _next_research_day(day: date, rhythm: Rhythm) -> date | None:
    for n in range(1, 15):
        candidate = day + timedelta(days=n)
        if rhythm.research(candidate):
            return candidate
    return None


def _offers(n: int) -> str:
    return "1 offre bien notée t'attend" if n == 1 else f"{n} offres bien notées t'attendent"


async def signal(session: AsyncSession, today: date) -> Signal | None:
    """Le message de fin de semaine, le dernier jour de recherche de la semaine ; None si ce
    n'est pas ce jour-là, en pause, ou sans objectif."""
    rhythm = await load(session)
    if not rhythm.research(today):
        return None
    if any(rhythm.research(today + timedelta(days=n)) for n in range(1, 7 - today.weekday())):
        return None
    current = await week(session, today)
    if not current.target:
        return None
    month = f"{today:%Y-%m}"
    week_start = max(today - timedelta(days=today.weekday()), today.replace(day=1))
    low = int(
        await session.scalar(
            select(func.count())
            .select_from(Application)
            .join(Evaluation, Evaluation.offer_id == Application.offer_id)
            .where(
                Application.orp_month == month,
                Application.sent_at >= week_start,
                Evaluation.score < LOW_SCORE,
            )
        )
        or 0
    )
    count, goal = current.count, current.target
    if count >= max(goal + 2, math.ceil(goal * TOO_MUCH)) and low >= LOW_MIN:
        return Signal(
            "too_much",
            f"{count} candidatures cette semaine, dont {low} peu notées",
            "Mieux vaut moins, mais mieux ciblé : garde ton énergie pour les offres qui te "
            "ressemblent.",
        )
    if count >= goal:
        target = await load_target(session)
        total = await _count(session, month, today.replace(day=1))
        name = MONTHS["fr"][today.month - 1].capitalize()
        return Signal(
            "done",
            f"Semaine faite : {count} candidature{'s' if count > 1 else ''}",
            f"{name} : {total} / {target}. Le reste du temps est à toi.",
        )
    following = _next_research_day(today, rhythm)
    to_review = int(
        await session.scalar(
            select(func.count())
            .select_from(Offer)
            .join(Evaluation, Evaluation.offer_id == Offer.id)
            .where(
                Offer.status.in_((OfferStatus.NEW, OfferStatus.TO_REVIEW)),
                Offer.expired_at.is_(None),
                Offer.duplicate_of.is_(None),
                Evaluation.score.is_not(None),
            )
        )
        or 0
    )
    when = DAY_NAMES[following.weekday()].capitalize() if following else "Au retour"
    waiting = (
        f"{when}, {_offers(min(to_review, DOSE))}."
        if to_review
        else f"{when}, reprends à ton rythme."
    )
    return Signal("late", f"{count} sur {goal} cette semaine", waiting)
