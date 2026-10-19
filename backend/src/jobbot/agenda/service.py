"""Tes dates dans ton agenda (docs/40) : entretiens, suites attendues, remise ORP, relances,
rendez-vous ORP (docs/83).

Le minimum : entreprise, poste et date ; ni adresse, ni contact, ni note. Un fichier par
entretien, ou un abonnement protégé par un jeton secret révocable.
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.agenda.ics import Event
from jobbot.auth.service import token_hash
from jobbot.core.orp import due_date, shift_month
from jobbot.db.models import (
    Application,
    ApplicationStatus,
    CalendarToken,
    Interview,
    OrpMeeting,
    OrpMonth,
)
from jobbot.followups.service import FOLLOW_UP_AFTER, local_today
from jobbot.letters.document import MONTHS
from jobbot.orp.service import load_due_day

PREFIX = "jba_"
INTERVIEW_ALARMS = ("P1D", "PT2H")
# Relance proposée jusqu'à 30 jours après l'envoi ; dossiers clos retirés (revue 0.33.1).
FOLLOW_UP_UNTIL = timedelta(days=30)
CLOSED = (ApplicationStatus.REFUS, ApplicationStatus.ENGAGEMENT, ApplicationStatus.SANS_REPONSE)
DUE_ALARMS = ("P3D",)


def _of_month(month: str) -> str:
    """« de septembre 2026 », « d'octobre 2026 » (élision devant une voyelle)."""
    year, number = month.split("-")
    name = MONTHS["fr"][int(number) - 1]
    prefix = "d'" if name[0] in "aeiouy" else "de "
    return f"{prefix}{name} {year}"


def interview_event(application: Application, base_url: str) -> Event | None:
    if application.interview_at is None:
        return None
    return Event(
        uid=f"interview-{application.id}@joba1",
        summary=f"Entretien \u2013 {application.company}",
        start=application.interview_at,
        description=application.job_title,
        url=f"{base_url}/candidatures/suivi",
        alarms=INTERVIEW_ALARMS,
    )


async def events(session: AsyncSession, base_url: str) -> list[Event]:
    """Tout ce qui va dans l'abonnement, dans l'ordre des dates."""
    found: list[Event] = []
    today = local_today()
    since = datetime.now(UTC) - timedelta(days=30)
    applications = list(await session.scalars(select(Application)))
    for application in applications:
        if application.status in CLOSED:
            continue
        meeting = interview_event(application, base_url)
        if meeting is not None and application.interview_at and application.interview_at >= since:
            found.append(meeting)
        # Relance à faire : le jour où la candidature atteint 10 jours sans réponse (docs/38).
        if (
            application.status == ApplicationStatus.EN_ATTENTE
            and application.sent_at + FOLLOW_UP_UNTIL >= today
        ):
            found.append(
                Event(
                    uid=f"follow-up-{application.id}@joba1",
                    summary=f"Relancer {application.company} ?",
                    start=max(application.sent_at + FOLLOW_UP_AFTER, today),
                    description=application.job_title,
                    url=f"{base_url}/candidatures/suivi",
                )
            )
    # Suites attendues après un entretien (docs/23).
    companies = {a.id: (a.company, a.job_title) for a in applications if a.status not in CLOSED}
    for interview in await session.scalars(
        select(Interview).where(
            Interview.next_step_at.is_not(None), Interview.next_step_at >= today - timedelta(days=7)
        )
    ):
        if interview.next_step in (None, "rien") or interview.application_id not in companies:
            continue
        company, title = companies[interview.application_id]
        assert interview.next_step_at is not None
        found.append(
            Event(
                uid=f"next-step-{interview.id}@joba1",
                summary=f"Suite attendue \u2013 {company}",
                start=interview.next_step_at,
                description=title,
                url=f"{base_url}/candidatures/suivi",
            )
        )
    # Remise des preuves ORP : mois précédent et mois en cours, tant qu'ils ne sont pas remis.
    due_day = await load_due_day(session)
    current = f"{today:%Y-%m}"
    months = {a.orp_month for a in applications}
    for month in (shift_month(current, -1), current):
        record = await session.get(OrpMonth, month)
        if month not in months or (record is not None and record.submitted_at):
            continue
        day = due_date(month, due_day)
        found.append(
            Event(
                uid=f"orp-{month}@joba1",
                summary=f"Preuves ORP {_of_month(month)} à remettre",
                start=day,
                url=f"{base_url}/candidatures/suivi",
                alarms=DUE_ALARMS,
            )
        )
    # Rendez-vous ORP : la date seulement, ni lieu ni conseiller.
    for appointment in await session.scalars(
        select(OrpMeeting).where(OrpMeeting.starts_at >= since)
    ):
        found.append(
            Event(
                uid=f"orp-meeting-{appointment.id}@joba1",
                summary="Rendez-vous ORP",
                start=appointment.starts_at,
                url=f"{base_url}/candidatures/rendez-vous-orp",
                alarms=INTERVIEW_ALARMS,
            )
        )
    return sorted(found, key=lambda e: (str(e.start)[:10], e.uid))


async def create_token(
    session: AsyncSession, name: str, origin: str | None
) -> tuple[CalendarToken, str]:
    token = PREFIX + secrets.token_urlsafe(24)
    row = CalendarToken(name=name, token_hash=token_hash(token), origin=origin)
    session.add(row)
    await session.flush()
    return row, token


async def authenticate(session: AsyncSession, token: str) -> CalendarToken | None:
    if not token.startswith(PREFIX):
        return None
    row = await session.scalar(
        select(CalendarToken).where(
            CalendarToken.token_hash == token_hash(token), CalendarToken.revoked_at.is_(None)
        )
    )
    if row is not None:
        row.last_used_at = datetime.now(UTC)
    return row
