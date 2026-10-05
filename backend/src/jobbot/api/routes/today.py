"""Page « Aujourd'hui » : liste de démarrage et point du jour (docs/10-ergonomie.md §2 b)."""

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from jobbot.core.orp import LOCAL_TZ, due_date, shift_month
from jobbot.db.models import (
    Application,
    ApplicationStatus,
    Criterion,
    Document,
    JobRun,
    JobRunStatus,
    Offer,
    OfferStatus,
    OrpMonth,
    ProfileChunk,
    Setting,
)
from jobbot.letters.service import load_identity
from jobbot.runtime import Runtime
from jobbot.worker.tasks.collect import COLLECT_JOB

router = APIRouter(prefix="/api", tags=["today"])
REMIND_AFTER = timedelta(days=10)

Step = Literal["criteria", "profile", "identity", "orp_target", "notifications", "imap"]


class ChecklistItem(BaseModel):
    key: Step
    done: bool


class TodayOut(BaseModel):
    # Démarrage : affiché tant qu'une étape manque, sauf si Kevin l'a masqué.
    checklist: list[ChecklistItem]
    checklist_dismissed: bool
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


class OnboardingIn(BaseModel):
    dismissed: bool


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


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
                    Setting.key.in_(("orp_monthly_target", "onboarding_dismissed"))
                )
            )
        }
        to_review = await count(
            select(func.count())
            .select_from(Offer)
            .where(
                Offer.status.in_((OfferStatus.NEW, OfferStatus.TO_REVIEW)),
                Offer.expired_at.is_(None),
            )
        )
        month_count = await count(
            select(func.count()).select_from(Application).where(Application.orp_month == month)
        )
        to_follow_up = await count(
            select(func.count())
            .select_from(Application)
            .where(
                Application.status == ApplicationStatus.EN_ATTENTE,
                Application.sent_at <= today - REMIND_AFTER,
            )
        )
        previous_count = await count(
            select(func.count()).select_from(Application).where(Application.orp_month == previous)
        )
        previous_record = await session.get(OrpMonth, previous)
        last_collect_at = await session.scalar(
            select(func.max(JobRun.finished_at)).where(
                JobRun.job == COLLECT_JOB, JobRun.status == JobRunStatus.SUCCESS
            )
        )

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
    return TodayOut(
        checklist=checklist,
        checklist_dismissed=bool(values.get("onboarding_dismissed")),
        to_review=to_review,
        month=month,
        month_count=month_count,
        month_target=int(target) if target else None,
        to_follow_up=to_follow_up,
        orp_due_month=due_month,
        orp_due_date=due_date(due_month) if due_month else None,
        last_collect_at=last_collect_at,
    )


@router.put("/onboarding", operation_id="setOnboarding", status_code=status.HTTP_204_NO_CONTENT)
async def set_onboarding(request: Request, body: OnboardingIn) -> None:
    """Masque (ou réaffiche) la liste de démarrage."""
    async with _runtime(request).sessionmaker.begin() as session:
        await session.execute(
            insert(Setting)
            .values(key="onboarding_dismissed", value=body.dismissed)
            .on_conflict_do_update(index_elements=["key"], set_={"value": body.dismissed})
        )
