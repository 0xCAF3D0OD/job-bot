"""Après le rendez-vous ORP (docs/83 §1, 0.67.2) : ce qui a été convenu, et le carnet.

Noter ce qui a été convenu met jobA1 à jour tout seul :
- le nouvel objectif mensuel remplace l'ancien ;
- une formation accordée passe en « financement accepté » ;
- le rendez-vous suivant est créé, et rejoint l'agenda et le rappel de la veille.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import OrpMeeting, Setting, Training, TrainingMark

# Le carnet : les rendez-vous passés, du plus récent au plus ancien.
LOG_SIZE = 24


@dataclass
class Measure:
    text: str
    training_id: int | None = None


@dataclass
class Outcome:
    target: int | None
    measures: list[Measure]
    assignments: str | None
    note: str | None
    next_starts_at: datetime | None = None


@dataclass(frozen=True)
class FollowedTraining:
    id: int
    title: str
    accepted: bool


def _start_of_day(now: datetime) -> datetime:
    return now.astimezone(LOCAL_TZ).replace(hour=0, minute=0, second=0, microsecond=0)


async def past(session: AsyncSession, now: datetime) -> list[OrpMeeting]:
    """Les rendez-vous d'avant aujourd'hui : celui du jour reste « le prochain »."""
    return list(
        await session.scalars(
            select(OrpMeeting)
            .where(OrpMeeting.starts_at < _start_of_day(now))
            .order_by(OrpMeeting.starts_at.desc())
            .limit(LOG_SIZE)
        )
    )


async def followed_trainings(session: AsyncSession) -> list[FollowedTraining]:
    """Les formations suivies ou envisagées : celles qu'une mesure peut accorder."""
    rows = (
        await session.execute(
            select(Training.id, Training.title, TrainingMark.funding_status)
            .join(TrainingMark, TrainingMark.training_id == Training.id)
            .order_by(Training.title)
        )
    ).all()
    found: dict[int, FollowedTraining] = {}
    for training_id, title, funding in rows:
        found.setdefault(training_id, FollowedTraining(training_id, title, funding == "accepted"))
    return list(found.values())


def _clean(value: str | None) -> str | None:
    return (value or "").strip() or None


async def save(
    session: AsyncSession, meeting: OrpMeeting, outcome: Outcome, now: datetime | None = None
) -> None:
    moment = now or datetime.now(UTC)
    followed = {t.id for t in await followed_trainings(session)}
    measures = [
        Measure(m.text.strip(), m.training_id if m.training_id in followed else None)
        for m in outcome.measures
        if m.text.strip()
    ]
    meeting.outcome_at = meeting.outcome_at or moment
    meeting.agreed_target = outcome.target
    meeting.measures = [m.__dict__ for m in measures]
    meeting.assignments = _clean(outcome.assignments)
    meeting.note = _clean(outcome.note)
    if outcome.target:
        await session.execute(
            insert(Setting)
            .values(key="orp_monthly_target", value=outcome.target)
            .on_conflict_do_update(
                index_elements=["user_id", "key"], set_={"value": outcome.target}
            )
        )
    granted = [m.training_id for m in measures if m.training_id is not None]
    if granted:
        await session.execute(
            update(TrainingMark)
            .where(TrainingMark.training_id.in_(granted))
            .values(funding_status="accepted", funding_reminded_at=None)
        )
    if outcome.next_starts_at is not None and outcome.next_starts_at > meeting.starts_at:
        # Le rendez-vous suivant : créé, ou déplacé s'il était déjà noté.
        following = await session.scalar(
            select(OrpMeeting)
            .where(OrpMeeting.starts_at > meeting.starts_at, OrpMeeting.id != meeting.id)
            .order_by(OrpMeeting.starts_at)
            .limit(1)
        )
        if following is None:
            following = OrpMeeting(
                place=meeting.place, advisor=meeting.advisor, questions=[], measures=[]
            )
            session.add(following)
        following.starts_at = outcome.next_starts_at


async def following(session: AsyncSession, meeting: OrpMeeting) -> datetime | None:
    """La date du rendez-vous suivant celui-ci, s'il est noté."""
    return await session.scalar(
        select(OrpMeeting.starts_at)
        .where(OrpMeeting.starts_at > meeting.starts_at, OrpMeeting.id != meeting.id)
        .order_by(OrpMeeting.starts_at)
        .limit(1)
    )
