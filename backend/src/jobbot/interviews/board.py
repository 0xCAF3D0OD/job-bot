"""Tableau des retours d'entretien (décision de Kevin du 17.11.2026) : lecture seule.

Une ligne par retour « Faire le point » enregistré, plus une ligne pour l'entretien prévu d'une
candidature qui n'a pas encore son retour. Aucune écriture, aucun appel à l'IA, aucun journal :
la RLS du compte en cours fait le tri (C-1, C-5).
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import Application, ApplicationStatus, Interview

PAGE_SIZE = 20

# « point » : ton retour « Faire le point » ; « issue » : la réponse de l'entreprise.
Point = Literal["a_venir", "a_faire", "fait"]
Issue = Literal["en_attente", "retenu", "pas_retenu"]


@dataclass
class Line:
    interview_id: int | None
    application_id: int
    company: str
    job_title: str
    day: date
    kind: str | None
    rating: int | None
    stress: int | None
    outlook: str | None
    next_step: str | None
    next_step_at: date | None
    thanks_sent: bool | None
    point: Point
    issue: Issue
    questions_count: int


def issue_of(application: Application) -> Issue:
    if application.status == ApplicationStatus.REFUS:
        return "pas_retenu"
    if application.status == ApplicationStatus.ENGAGEMENT:
        return "retenu"
    return "en_attente"


def _local_day(at: datetime) -> date:
    return at.astimezone(LOCAL_TZ).date()


def _done(application: Application, review: Interview) -> Line:
    if review.held_at is not None:
        day = review.held_at
    elif application.interview_at is not None:
        day = _local_day(application.interview_at)
    else:
        day = _local_day(review.created_at)
    return Line(
        interview_id=review.id,
        application_id=application.id,
        company=application.company,
        job_title=application.job_title,
        day=day,
        kind=review.kind,
        rating=review.rating,
        stress=review.stress,
        outlook=review.outlook,
        next_step=review.next_step,
        next_step_at=review.next_step_at,
        thanks_sent=review.thanks == "sent",
        point="fait",
        issue=issue_of(application),
        questions_count=len(review.questions or []),
    )


def _planned(application: Application, at: datetime, now: datetime) -> Line:
    return Line(
        interview_id=None,
        application_id=application.id,
        company=application.company,
        job_title=application.job_title,
        day=_local_day(at),
        kind=None,
        rating=None,
        stress=None,
        outlook=None,
        next_step=None,
        next_step_at=None,
        thanks_sent=None,
        point="a_venir" if at > now else "a_faire",
        issue=issue_of(application),
        questions_count=0,
    )


async def lines(session: AsyncSession, now: datetime | None = None) -> list[Line]:
    """Toutes les lignes du compte, de la plus récente à la plus ancienne."""
    now = now or datetime.now(UTC)
    reviews: dict[int, list[Interview]] = {}
    for review in await session.scalars(
        select(Interview).where(Interview.reviewed()).order_by(Interview.id)
    ):
        reviews.setdefault(review.application_id, []).append(review)
    applications = await session.scalars(
        select(Application).where(
            Application.interview_at.is_not(None) | Application.id.in_(list(reviews))
        )
    )
    found: list[Line] = []
    for application in applications:
        done = [_done(application, r) for r in reviews.get(application.id, [])]
        found.extend(done)
        at = application.interview_at
        if at is None:
            continue
        # L'entretien prévu n'a pas encore son retour : aucun retour du tout, ou un entretien
        # à venir plus tard que le dernier retour (le suivant d'une même candidature).
        if not done or (at > now and _local_day(at) > max(line.day for line in done)):
            found.append(_planned(application, at, now))
    found.sort(
        key=lambda line: (line.day, line.interview_id or 0, line.application_id), reverse=True
    )
    return found


async def page(session: AsyncSession, offset: int) -> tuple[list[Line], int]:
    """Une page de 20 lignes et le total."""
    every = await lines(session)
    return every[offset : offset + PAGE_SIZE], len(every)


async def detail(session: AsyncSession, interview_id: int) -> tuple[Interview, Application] | None:
    """Le retour complet et sa candidature, ou rien s'il n'est pas à ce compte (RLS)."""
    review = await session.get(Interview, interview_id)
    if review is None:
        return None
    application = await session.get(Application, review.application_id)
    if application is None:
        return None
    return review, application
