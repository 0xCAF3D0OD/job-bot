"""Notifications ntfy (docs/06-note-ia.md §5).

- Nouvelles offres dont la note atteint le seuil des Réglages : une notification groupée
  par passage, une seule fois par offre.
- Dépense de l'IA à 80 % du plafond mensuel : une notification par mois.

Envoi en JSON (UTF-8 sûr pour les accents), au serveur JOBBOT_NTFY_URL, sur le sujet
secret JOBBOT_NTFY_TOPIC. Sans sujet, rien n'est envoyé.
"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from jobbot.db.models import (
    Application,
    ApplicationStatus,
    Evaluation,
    Offer,
    OfferStatus,
    Setting,
)
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.scoring.service import budget_state
from jobbot.settings import Settings

log = get_logger(__name__)

MAX_LISTED = 8
BUDGET_ALERT_RATIO = Decimal("0.8")
BUDGET_ALERT_KEY = "budget_alert_month"


@dataclass(frozen=True)
class Message:
    title: str
    message: str
    priority: int = 3
    tags: list[str] = field(default_factory=list)
    click: str | None = None


async def http_send(settings: Settings, message: Message) -> None:
    topic = settings.ntfy_topic.get_secret_value() if settings.ntfy_topic else ""
    payload: dict[str, Any] = {
        "topic": topic,
        "title": message.title,
        "message": message.message,
        "priority": message.priority,
        "tags": message.tags,
    }
    if message.click:
        payload["click"] = message.click
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(settings.ntfy_url.rstrip("/"), json=payload)
        response.raise_for_status()


# Remplaçable en test : aucun envoi réel.
send: Callable[[Settings, Message], Awaitable[None]] = http_send


def offers_message(
    settings: Settings, rows: Sequence[tuple[int, str, str | None, str | None]]
) -> Message:
    """rows : (note, titre, entreprise, lieu), meilleures notes d'abord."""
    lines = [
        f"{score} · {title}"
        + (f" — {company}" if company else "")
        + (f" ({location})" if location else "")
        for score, title, company, location in rows[:MAX_LISTED]
    ]
    if len(rows) > MAX_LISTED:
        lines.append(f"… et {len(rows) - MAX_LISTED} autre(s)")
    best = rows[0][0]
    return Message(
        title=f"{len(rows)} nouvelle(s) offre(s) pour toi (jusqu'à {best}/100)",
        message="\n".join(lines),
        priority=4 if best >= 85 else 3,
        tags=["briefcase"],
        click=f"{settings.public_url.rstrip('/')}/offres?tri=score",
    )


@dataclass
class NotifyResult:
    configured: bool = True
    offers: int = 0
    budget_alert: bool = False


async def _threshold(runtime: Runtime) -> int:
    async with runtime.sessionmaker() as session:
        value = await session.scalar(
            select(Setting.value).where(Setting.key == "notify_score_threshold")
        )
    return int(value) if value is not None else 70


async def notify_new_scores(runtime: Runtime) -> NotifyResult:
    settings = runtime.settings
    if not settings.ntfy_configured:
        return NotifyResult(configured=False)
    result = NotifyResult()
    threshold = await _threshold(runtime)
    async with runtime.sessionmaker() as session:
        rows = (
            await session.execute(
                select(Evaluation.id, Evaluation.score, Offer.title, Offer.company, Offer.location)
                .join(Offer, Offer.id == Evaluation.offer_id)
                .where(
                    Evaluation.notified_at.is_(None),
                    Evaluation.scored_at.is_not(None),
                    Evaluation.score >= threshold,
                    Offer.status.in_((OfferStatus.NEW, OfferStatus.TO_REVIEW)),
                )
                .order_by(Evaluation.score.desc(), Offer.first_seen_at.desc())
            )
        ).all()
    if rows:
        await send(
            settings, offers_message(settings, [(r[1] or 0, r[2], r[3], r[4]) for r in rows])
        )
        async with runtime.sessionmaker.begin() as session:
            await session.execute(
                update(Evaluation)
                .where(Evaluation.id.in_([r[0] for r in rows]))
                .values(notified_at=datetime.now(UTC))
            )
        result.offers = len(rows)

    # Les notes trop basses ne seront jamais signalées : on les marque aussi, pour ne
    # pas les signaler si le seuil baisse plus tard (seules les nouvelles notes comptent).
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Evaluation)
            .where(Evaluation.notified_at.is_(None), Evaluation.scored_at.is_not(None))
            .values(notified_at=datetime.now(UTC))
        )

    result.budget_alert = await _budget_alert(runtime)
    if result.offers or result.budget_alert:
        log.info("notifications_sent", offers=result.offers, budget_alert=result.budget_alert)
    return result


async def _budget_alert(runtime: Runtime) -> bool:
    now = datetime.now(UTC)
    month = now.strftime("%Y-%m")
    async with runtime.sessionmaker() as session:
        spend, budget, _ = await budget_state(session, now)
        already = await session.scalar(select(Setting.value).where(Setting.key == BUDGET_ALERT_KEY))
    if budget <= 0 or spend < budget * BUDGET_ALERT_RATIO or already == month:
        return False
    await send(
        runtime.settings,
        Message(
            title="Budget de l'IA presque atteint",
            message=f"{spend:.2f} CHF dépensés sur {budget:.2f} CHF ce mois-ci. "
            "Au-delà du plafond, les offres ne sont plus notées jusqu'au mois prochain.",
            priority=4,
            tags=["warning"],
            click=f"{runtime.settings.public_url.rstrip('/')}/reglages",
        ),
    )
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            insert(Setting)
            .values(key=BUDGET_ALERT_KEY, value=month)
            .on_conflict_do_update(index_elements=["key"], set_={"value": month})
        )
    return True


async def send_test(settings: Settings) -> None:
    await send(
        settings,
        Message(
            title="job-bot : notification de test",
            message="Les notifications fonctionnent. Tu seras prévenu des offres bien notées.",
            tags=["white_check_mark"],
            click=f"{settings.public_url.rstrip('/')}/offres",
        ),
    )


# --- Relances (0.5) -------------------------------------------------------------------

REMIND_AFTER_DAYS = 10


async def notify_reminders(runtime: Runtime, today: date | None = None) -> int:
    """Candidatures en attente depuis 10 jours : une notification groupée, une seule fois
    par candidature. Sans ntfy configuré, rien n'est marqué (le rappel reste à faire)."""
    settings = runtime.settings
    if not settings.ntfy_configured:
        return 0
    today = today or datetime.now(UTC).date()
    limit = today - timedelta(days=REMIND_AFTER_DAYS)
    async with runtime.sessionmaker() as session:
        due = list(
            await session.scalars(
                select(Application)
                .where(
                    Application.status == ApplicationStatus.EN_ATTENTE,
                    Application.reminded_at.is_(None),
                    Application.sent_at <= limit,
                )
                .order_by(Application.sent_at)
            )
        )
    if not due:
        return 0
    lines = [
        f"{a.company} — {a.job_title} (envoyée le {a.sent_at:%d.%m})" for a in due[:MAX_LISTED]
    ]
    if len(due) > MAX_LISTED:
        lines.append(f"… et {len(due) - MAX_LISTED} autre(s)")
    await send(
        settings,
        Message(
            title=f"{len(due)} candidature(s) sans réponse depuis {REMIND_AFTER_DAYS} jours",
            message="Relancer ?\n" + "\n".join(lines),
            tags=["hourglass"],
            click=f"{settings.public_url.rstrip('/')}/candidatures",
        ),
    )
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Application)
            .where(Application.id.in_([a.id for a in due]))
            .values(reminded_at=datetime.now(UTC))
        )
    log.info("reminders_sent", applications=len(due))
    return len(due)
