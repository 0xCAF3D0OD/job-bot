"""Les formules (docs/125) : Essentiel, gratuite, et Plus. On limite l'IA, pas l'accès : tout
ce qui n'appelle pas l'IA reste illimité, et le cycle ORP est gratuit pour toujours. Les limites
sont des nombres par mois civil, comptés à partir des appels déjà enregistrés (`llm_calls`) ; le
plafond en francs reste le dernier garde-fou. L'exploitant n'a pas de limite."""

from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts
from jobbot.db.models import InterviewPractice, LlmCall, User

ESSENTIEL = "essentiel"
PLUS = "plus"
PLANS = (ESSENTIEL, PLUS)
PLUS_PRICE_CHF = 7

# Les usages limités, dans l'ordre où la personne les voit.
SCORE = "score"
LETTER = "letter"
CV = "cv"
CHAT = "chat"
PRACTICE = "practice"
LIMITS: dict[str, dict[str, int]] = {
    ESSENTIEL: {SCORE: 150, LETTER: 10, CV: 10, CHAT: 30, PRACTICE: 1},
    PLUS: {SCORE: 600, LETTER: 60, CV: 60, CHAT: 300, PRACTICE: 8},
}
# Le nom de l'usage, au pluriel, comme il s'affiche (« 37 offres notées sur 150 »).
LABELS = {
    SCORE: "offres notées",
    LETTER: "lettres",
    CV: "CV adaptés",
    CHAT: "messages à l'assistant",
    PRACTICE: "entraînements à l'entretien",
}


@dataclass(frozen=True)
class Usage:
    key: str
    label: str
    used: int
    limit: int | None  # None : sans limite (l'exploitant)

    @property
    def left(self) -> int | None:
        return None if self.limit is None else max(0, self.limit - self.used)


def month_start(now: datetime | None = None) -> datetime:
    now = now or datetime.now(UTC)
    return now.astimezone(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def resets_on(now: datetime | None = None) -> date:
    start = month_start(now)
    return date(start.year + start.month // 12, start.month % 12 + 1, 1)


async def plan_of(session: AsyncSession, today: date | None = None) -> str:
    """Plus offert (sans date) ou payé jusqu'à `plan_until` ; passé cette date, Essentiel."""
    row = (
        await session.execute(
            select(User.plan, User.plan_until).where(User.id == accounts.current())
        )
    ).first()
    if row is None or row.plan not in PLANS:
        return ESSENTIEL
    today = today or datetime.now(UTC).date()
    if row.plan == PLUS and row.plan_until is not None and row.plan_until < today:
        return ESSENTIEL
    return str(row.plan)


async def used(session: AsyncSession, key: str, now: datetime | None = None) -> int:
    start = month_start(now)
    if key == SCORE:
        # Une offre compte une fois par mois, même renotée (profil changé, « Je l'ai »).
        query = select(func.count(distinct(LlmCall.offer_id))).where(
            LlmCall.purpose == SCORE, LlmCall.offer_id.is_not(None), LlmCall.created_at >= start
        )
    elif key == PRACTICE:
        # Une séance, quel que soit le nombre de questions.
        query = (
            select(func.count())
            .select_from(InterviewPractice)
            .where(InterviewPractice.created_at >= start)
        )
    else:
        query = select(func.count()).where(LlmCall.purpose == key, LlmCall.created_at >= start)
    return int(await session.scalar(query) or 0)


async def usage(session: AsyncSession, now: datetime | None = None) -> list[Usage]:
    owner = await accounts.is_owner(session)
    limits = LIMITS[await plan_of(session)]
    return [
        Usage(key, LABELS[key], await used(session, key, now), None if owner else limit)
        for key, limit in limits.items()
    ]


async def left(session: AsyncSession, key: str, now: datetime | None = None) -> int | None:
    """Ce qui reste ce mois-ci pour un usage ; None sans limite (l'exploitant)."""
    if await accounts.is_owner(session):
        return None
    limit = LIMITS[await plan_of(session)][key]
    return max(0, limit - await used(session, key, now))


async def scored_this_month(session: AsyncSession, now: datetime | None = None) -> set[int]:
    rows = await session.scalars(
        select(LlmCall.offer_id)
        .distinct()
        .where(
            LlmCall.purpose == SCORE,
            LlmCall.offer_id.is_not(None),
            LlmCall.created_at >= month_start(now),
        )
    )
    return {r for r in rows if r is not None}


# Les usages au féminin (« utilisées », « elles »), et au singulier pour une limite de 1.
FEMININE = {SCORE, LETTER}
SINGULAR = {
    SCORE: "offre notée",
    LETTER: "lettre",
    CV: "CV adapté",
    CHAT: "message à l'assistant",
    PRACTICE: "entraînement à l'entretien",
}


class LimitReached(Exception):
    """Les usages du mois sont épuisés : le message dit lesquels et quand ils reviennent."""

    def __init__(self, key: str, limit: int, now: datetime | None = None) -> None:
        self.key = key
        day = resets_on(now)
        when = f"le {day.day}{'er' if day.day == 1 else ''} {MONTHS[day.month - 1]}"
        feminine = key in FEMININE
        if limit == 1:
            the, e, it = ("La ", "e", "elle") if feminine else ("Le ", "", "il")
            if SINGULAR[key][0] in "aeiouéèêàâî":
                the = "L'"
            text = f"{the}{SINGULAR[key]} du mois est utilisé{e} : {it} revient {when}."
        else:
            e, they = ("es", "elles") if feminine else ("s", "ils")
            text = f"Les {limit} {LABELS[key]} du mois sont utilisé{e} : {they} reviennent {when}."
        super().__init__(text)


MONTHS = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)  # fmt: skip


async def check(session: AsyncSession, key: str) -> None:
    """Lève `LimitReached` si l'usage du mois est épuisé (rien pour l'exploitant)."""
    remaining = await left(session, key)
    if remaining == 0:
        raise LimitReached(key, LIMITS[await plan_of(session)][key])
