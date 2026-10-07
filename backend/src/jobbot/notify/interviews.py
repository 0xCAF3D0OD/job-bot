"""« Comment s'est passé ton entretien ? » (docs/23 §1) : le lendemain d'un entretien sans
retour, une alerte (cloche, et téléphone si ntfy est configuré), une fois par date."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import Application, ApplicationStatus, Interview
from jobbot.notify.service import Message, deliver
from jobbot.runtime import Runtime

LOCAL_TZ = ZoneInfo("Europe/Zurich")
# Au-delà, l'entretien est trop ancien pour en demander le retour.
LOOK_BACK = timedelta(days=14)


@dataclass(frozen=True)
class PendingFeedback:
    application_id: int
    company: str
    interview_on: date

    @property
    def link(self) -> str:
        day = self.interview_on
        return f"/candidatures/suivi?mois={day:%Y-%m}&jour={day.isoformat()}"


async def pending(session: AsyncSession, today: date) -> list[tuple[Application, date]]:
    """Entretiens passés (hier ou avant, 14 jours au plus) sans retour pour cette date."""
    rows = list(
        await session.scalars(
            select(Application).where(
                Application.status == ApplicationStatus.ENTRETIEN,
                Application.interview_at.is_not(None),
            )
        )
    )
    found: list[tuple[Application, date]] = []
    for application in rows:
        assert application.interview_at is not None
        day = application.interview_at.astimezone(LOCAL_TZ).date()
        if not (today - LOOK_BACK <= day < today):
            continue
        done = await session.scalar(
            select(Interview.id).where(
                Interview.application_id == application.id, Interview.held_at == day
            )
        )
        if done is None:
            found.append((application, day))
    return found


async def to_review(session: AsyncSession, today: date | None = None) -> list[PendingFeedback]:
    today = today or datetime.now(UTC).astimezone(LOCAL_TZ).date()
    return [PendingFeedback(a.id, a.company, day) for a, day in await pending(session, today)]


async def notify_interviews(runtime: Runtime, today: date | None = None) -> int:
    today = today or datetime.now(UTC).astimezone(LOCAL_TZ).date()
    async with runtime.sessionmaker() as session:
        due = [
            (a, day)
            for a, day in await pending(session, today)
            if a.interview_reminded_at != a.interview_at
        ]
    base = runtime.settings.public_url.rstrip("/")
    for application, day in due:
        item = PendingFeedback(application.id, application.company, day)
        await deliver(
            runtime,
            Message(
                title=f"Comment s'est passé ton entretien chez {application.company} ?",
                message="Fais le point en deux minutes : ce qui a marché, ce qui est à préparer.",
                tags=["speech_balloon"],
                click=f"{base}{item.link}",
            ),
            kind="interview",
            link=item.link,
        )
        async with runtime.sessionmaker.begin() as session:
            stored = await session.get(Application, application.id)
            if stored is not None:
                stored.interview_reminded_at = application.interview_at
    return len(due)
