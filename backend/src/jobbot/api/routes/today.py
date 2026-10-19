"""Page « Aujourd'hui » : liste de démarrage et point du jour (docs/10-ergonomie.md §2 b)."""

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Request, status
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.alerts import service as alert_service
from jobbot.contacts import service as contact_service
from jobbot.core.orp import LOCAL_TZ, due_date, shift_month
from jobbot.db.models import (
    Application,
    ApplicationStatus,
    Contact,
    Criterion,
    Document,
    JobRun,
    JobRunStatus,
    Offer,
    OfferStatus,
    OrpMonth,
    ProfileChunk,
    Search,
    Setting,
)
from jobbot.letters.service import load_identity
from jobbot.notify import interviews as interview_reminders
from jobbot.orp import meeting as orp_meeting
from jobbot.orp.service import load_due_day
from jobbot.rhythm import service as rhythm
from jobbot.runtime import Runtime
from jobbot.worker.tasks.collect import COLLECT_JOB

router = APIRouter(prefix="/api", tags=["today"])
REMIND_AFTER = timedelta(days=10)
NO_ANSWER_AFTER = timedelta(days=14)

Step = Literal["criteria", "profile", "identity", "orp_target", "notifications", "imap"]


class ChecklistItem(BaseModel):
    key: Step
    done: bool


class JourneyStep(BaseModel):
    """Une étape de « Comment ça marche » (docs/21 §3), cochée d'après les données."""

    key: Literal["alerts", "triage", "apply", "follow", "orp"]
    done: bool


class InterviewToReview(BaseModel):
    """Entretien passé sans retour (docs/23 §1)."""

    application_id: int
    company: str
    interview_on: date
    link: str


class UpcomingInterview(BaseModel):
    """Entretien aujourd'hui ou demain : en tête d'Aujourd'hui (docs/43 n° 30)."""

    application_id: int
    company: str
    at: datetime


class DayActivity(BaseModel):
    """Un jour de la semaine en tableau de bord (docs/54 §5)."""

    day: date
    offers: int
    applications: int


class MonthResult(BaseModel):
    """Un mois passé, pour la jauge de l'objectif ORP (docs/54 §5)."""

    month: str
    count: int


class RhythmDay(BaseModel):
    day: date
    research: bool
    sent: int


class RhythmWeek(BaseModel):
    """Le bon rythme (docs/86) : la part de l'objectif ORP pour cette semaine."""

    target: int | None
    count: int
    days: list[RhythmDay]
    research_today: bool


class TodayOut(BaseModel):
    # Démarrage : affiché tant qu'une étape manque, sauf si Kevin l'a masqué.
    checklist: list[ChecklistItem]
    checklist_dismissed: bool
    # « Comment ça marche » : le chemin en cinq étapes (docs/21 §3).
    journey: list[JourneyStep] = []
    journey_dismissed: bool = False
    to_review: int
    month: str
    month_count: int
    month_target: int | None
    # Candidatures en attente depuis 10 jours ou plus : à relancer.
    to_follow_up: int
    # Prochain mois ORP à remettre, s'il y en a un.
    orp_due_month: str | None
    orp_due_date: date | None
    last_collect_at: datetime | None
    # Alertes créées sur un site depuis 3 jours sans rien avoir envoyé (docs/20 §1.4).
    alerts_waiting: int = 0
    # Prises de contact sans réponse depuis 7 jours (docs/31 §4).
    contacts_to_follow_up: int = 0
    interviews_to_review: list[InterviewToReview] = []
    upcoming_interviews: list[UpcomingInterview] = []
    # Les 7 derniers jours (le plus ancien d'abord) et les 3 mois précédents (docs/54).
    week: list[DayActivity] = []
    orp_history: list[MonthResult] = []
    # Rendez-vous ORP aujourd'hui ou demain : la feuille est prête (docs/83).
    orp_meeting_at: datetime | None = None
    # Ta semaine (docs/86) : la part de l'objectif, et si aujourd'hui est un jour de recherche.
    rhythm: RhythmWeek | None = None


class OnboardingIn(BaseModel):
    dismissed: bool


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


async def _week(session: AsyncSession, today: date) -> list[DayActivity]:
    """Offres reçues (première fois vues, doublons exclus) et candidatures envoyées, par jour,
    sur les 7 derniers jours (heure suisse)."""
    first = today - timedelta(days=6)
    start = datetime.combine(first, datetime.min.time(), LOCAL_TZ)
    seen_day = func.date(func.timezone("Europe/Zurich", Offer.first_seen_at))
    offers: dict[date, int] = dict(
        (
            await session.execute(
                select(seen_day, func.count())
                .where(Offer.first_seen_at >= start, Offer.duplicate_of.is_(None))
                .group_by(seen_day)
            )
        ).all()
    )
    sent: dict[date, int] = dict(
        (
            await session.execute(
                select(Application.sent_at, func.count())
                .where(Application.sent_at >= first, Application.sent_at <= today)
                .group_by(Application.sent_at)
            )
        ).all()
    )
    days = [first + timedelta(days=i) for i in range(7)]
    return [
        DayActivity(day=d, offers=int(offers.get(d, 0)), applications=int(sent.get(d, 0)))
        for d in days
    ]


@router.get("/today", operation_id="getToday")
async def get_today(request: Request) -> TodayOut:
    runtime = _runtime(request)
    settings = runtime.settings
    today = datetime.now(UTC).astimezone(LOCAL_TZ).date()
    month = f"{today:%Y-%m}"
    previous = shift_month(month, -1)
    async with runtime.sessionmaker() as session:

        async def count(query: object) -> int:
            return int(await session.scalar(query) or 0)  # type: ignore[call-overload]

        criteria = await count(select(func.count()).select_from(Criterion))
        documents = await count(select(func.count()).select_from(Document))
        chunks = await count(
            select(func.count()).select_from(ProfileChunk).where(ProfileChunk.active.is_(True))
        )
        identity = await load_identity(session)
        values = {
            s.key: s.value
            for s in await session.scalars(
                select(Setting).where(
                    Setting.key.in_(
                        ("orp_monthly_target", "onboarding_dismissed", "journey_dismissed")
                    )
                )
            )
        }
        to_review = await count(
            select(func.count())
            .select_from(Offer)
            .where(
                Offer.status.in_((OfferStatus.NEW, OfferStatus.TO_REVIEW)),
                Offer.expired_at.is_(None),
                Offer.duplicate_of.is_(None),
            )
        )
        month_count = await count(
            select(func.count()).select_from(Application).where(Application.orp_month == month)
        )
        to_follow_up = await count(
            select(func.count())
            .select_from(Application)
            .where(
                or_(
                    and_(
                        Application.status == ApplicationStatus.EN_ATTENTE,
                        Application.sent_at <= today - REMIND_AFTER,
                    ),
                    # Relancées sans réponse depuis 14 jours : la même liste que le Suivi
                    # (docs/38 §4).
                    and_(
                        Application.status == ApplicationStatus.RELANCEE,
                        Application.followed_up_at <= today - NO_ANSWER_AFTER,
                    ),
                )
            )
        )
        previous_count = await count(
            select(func.count()).select_from(Application).where(Application.orp_month == previous)
        )
        previous_record = await session.get(OrpMonth, previous)
        due_day = await load_due_day(session)
        journey = [
            JourneyStep(
                key="alerts",
                done=await count(
                    select(func.count()).select_from(Search).where(Search.parse_status == "parsed")
                )
                > 0,
            ),
            JourneyStep(
                key="triage",
                done=await count(
                    select(func.count())
                    .select_from(Offer)
                    .where(
                        Offer.status.in_(
                            (
                                OfferStatus.LATER,
                                OfferStatus.IGNORED,
                                OfferStatus.PREPARING,
                                OfferStatus.APPLIED,
                            )
                        )
                    )
                )
                > 0,
            ),
            JourneyStep(
                key="apply", done=await count(select(func.count()).select_from(Application)) > 0
            ),
            JourneyStep(
                key="follow",
                done=await count(
                    select(func.count())
                    .select_from(Application)
                    .where(Application.status != ApplicationStatus.EN_ATTENTE)
                )
                > 0,
            ),
            JourneyStep(
                key="orp",
                done=await count(
                    select(func.count())
                    .select_from(OrpMonth)
                    .where(OrpMonth.submitted_at.is_not(None))
                )
                > 0,
            ),
        ]
        interviews_to_review = [
            InterviewToReview(
                application_id=p.application_id,
                company=p.company,
                interview_on=p.interview_on,
                link=p.link,
            )
            for p in await interview_reminders.to_review(session, today)
        ]
        # Entretiens d'ici la fin de demain (heure suisse), dossiers clos exceptés.
        now = datetime.now(UTC)
        until = datetime.combine(today + timedelta(days=2), datetime.min.time(), LOCAL_TZ)
        upcoming_interviews = [
            UpcomingInterview(application_id=a.id, company=a.company, at=a.interview_at)
            for a in await session.scalars(
                select(Application)
                .where(
                    Application.interview_at >= now,
                    Application.interview_at < until,
                    Application.status.not_in(
                        (
                            ApplicationStatus.REFUS,
                            ApplicationStatus.ENGAGEMENT,
                            ApplicationStatus.SANS_REPONSE,
                        )
                    ),
                )
                .order_by(Application.interview_at)
            )
            if a.interview_at is not None
        ]
        alerts_waiting = await alert_service.waiting(session)
        contacts_to_follow_up = await count(
            select(func.count())
            .select_from(Contact)
            .where(
                Contact.answered_on.is_(None),
                Contact.contacted_on <= today - contact_service.FOLLOW_UP_AFTER,
            )
        )
        last_collect_at = await session.scalar(
            select(func.max(JobRun.finished_at)).where(
                JobRun.job == COLLECT_JOB, JobRun.status == JobRunStatus.SUCCESS
            )
        )

        week = await _week(session, today)
        orp_history = [
            MonthResult(
                month=m,
                count=await count(
                    select(func.count()).select_from(Application).where(Application.orp_month == m)
                ),
            )
            for m in (shift_month(month, -3), shift_month(month, -2), previous)
        ]

    target = values.get("orp_monthly_target")
    checklist = [
        ChecklistItem(key="criteria", done=criteria > 0),
        ChecklistItem(key="profile", done=documents > 0 and chunks > 0),
        ChecklistItem(key="identity", done=not identity.missing),
        ChecklistItem(key="orp_target", done=bool(target)),
        ChecklistItem(key="notifications", done=settings.ntfy_configured),
        ChecklistItem(key="imap", done=settings.imap_configured),
    ]
    due_month = (
        previous
        if previous_count and (previous_record is None or not previous_record.submitted_at)
        else None
    )
    async with runtime.sessionmaker() as session:
        meeting = await orp_meeting.next_meeting(session, datetime.now(UTC))
        this_week = await rhythm.week(session, rhythm.local_today())
    soon = meeting is not None and (
        meeting.starts_at.astimezone(LOCAL_TZ).date()
        - datetime.now(UTC).astimezone(LOCAL_TZ).date()
    ) <= timedelta(days=1)
    return TodayOut(
        checklist=checklist,
        checklist_dismissed=bool(values.get("onboarding_dismissed")),
        journey=journey,
        journey_dismissed=bool(values.get("journey_dismissed")),
        to_review=to_review,
        month=month,
        month_count=month_count,
        month_target=int(target) if target else None,
        to_follow_up=to_follow_up,
        orp_due_month=due_month,
        orp_due_date=due_date(due_month, due_day) if due_month else None,
        last_collect_at=last_collect_at,
        alerts_waiting=alerts_waiting,
        contacts_to_follow_up=contacts_to_follow_up,
        interviews_to_review=interviews_to_review,
        upcoming_interviews=upcoming_interviews,
        week=week,
        orp_history=orp_history,
        orp_meeting_at=meeting.starts_at if meeting is not None and soon else None,
        rhythm=RhythmWeek(
            target=this_week.target,
            count=this_week.count,
            days=[RhythmDay(day=d.day, research=d.research, sent=d.sent) for d in this_week.days],
            research_today=this_week.research_today,
        ),
    )


@router.put("/onboarding", operation_id="setOnboarding", status_code=status.HTTP_204_NO_CONTENT)
async def set_onboarding(request: Request, body: OnboardingIn) -> None:
    """Masque (ou réaffiche) la liste de démarrage."""
    async with _runtime(request).sessionmaker.begin() as session:
        await session.execute(
            insert(Setting)
            .values(key="onboarding_dismissed", value=body.dismissed)
            .on_conflict_do_update(
                index_elements=["user_id", "key"], set_={"value": body.dismissed}
            )
        )


@router.put("/journey", operation_id="setJourney", status_code=status.HTTP_204_NO_CONTENT)
async def set_journey(request: Request, body: OnboardingIn) -> None:
    """Masque (ou réaffiche) « Comment ça marche »."""
    async with _runtime(request).sessionmaker.begin() as session:
        await session.execute(
            insert(Setting)
            .values(key="journey_dismissed", value=body.dismissed)
            .on_conflict_do_update(
                index_elements=["user_id", "key"], set_={"value": body.dismissed}
            )
        )
