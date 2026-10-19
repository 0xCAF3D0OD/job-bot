"""Le rappel de la veille d'un rendez-vous ORP (docs/83 §1) : dans la cloche, et sur le
téléphone si ntfy est configuré. Une fois par date : un rendez-vous déplacé est rappelé à
nouveau."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import OrpMeeting
from jobbot.notify.service import Message, deliver
from jobbot.runtime import Runtime

LINK = "/candidatures/rendez-vous-orp"


async def notify_orp_meeting(runtime: Runtime, now: datetime | None = None) -> int:
    moment = (now or datetime.now(UTC)).astimezone(LOCAL_TZ)
    tomorrow = moment.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    async with runtime.sessionmaker() as session:
        due = [
            m
            for m in await session.scalars(
                select(OrpMeeting).where(
                    OrpMeeting.starts_at >= tomorrow,
                    OrpMeeting.starts_at < tomorrow + timedelta(days=1),
                )
            )
            if m.reminded_for != m.starts_at
        ]
    base = runtime.settings.public_url.rstrip("/")
    for meeting in due:
        at = meeting.starts_at.astimezone(LOCAL_TZ)
        await deliver(
            runtime,
            Message(
                title=f"Demain à {at:%H:%M} : rendez-vous ORP",
                message="Ta feuille est prête : ce qui bloque, tes questions, tes obligations.",
                tags=["handshake"],
                click=f"{base}{LINK}",
            ),
            kind="orp_meeting",
            link=LINK,
        )
        async with runtime.sessionmaker.begin() as session:
            stored = await session.get(OrpMeeting, meeting.id)
            if stored is not None:
                stored.reminded_for = meeting.starts_at
    return len(due)
