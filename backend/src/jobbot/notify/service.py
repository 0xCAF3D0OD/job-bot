"""Notifications ntfy (docs/06-note-ia.md §5).

- Nouvelles offres dont la note atteint le seuil des Réglages : une notification groupée
  par passage, une seule fois par offre.
- Dépense de l'IA à 80 % du plafond mensuel : une notification par mois.
- Le bon rythme (docs/86) : par défaut, les offres arrivent en un seul message par jour, dès
  l'heure choisie, un jour de recherche ; les jours de repos, rien ne part vers le
  téléphone, sauf les rappels qui ont une date limite (la cloche garde tout).

Envoi en JSON (UTF-8 sûr pour les accents), au serveur JOBBOT_NTFY_URL, sur le sujet
secret JOBBOT_NTFY_TOPIC. Sans sujet, rien ne part vers le téléphone ; chaque alerte est aussi
enregistrée pour la cloche de la plateforme (docs/15 §1).
"""

import secrets
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import httpx
from pydantic import SecretStr
from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts
from jobbot.core.orp import LOCAL_TZ
from jobbot.core.plural import plural
from jobbot.db.models import (
    Application,
    Evaluation,
    Notification,
    Offer,
    OfferStatus,
    Setting,
)
from jobbot.followups.remind import REMIND_AFTER_DAYS, remind_due
from jobbot.log import get_logger
from jobbot.rhythm import service as rhythm
from jobbot.runtime import Runtime
from jobbot.scoring.service import budget_state
from jobbot.settings import Settings

log = get_logger(__name__)

MAX_LISTED = 8
BUDGET_ALERT_RATIO = Decimal("0.8")
BUDGET_ALERT_KEY = "budget_alert_month"
DIGEST_KEY = "offers_digest_day"
# Ce qui peut attendre un jour de recherche (docs/86 §2) ; les rappels datés (remise ORP,
# rendez-vous de demain) et les alertes techniques passent toujours.
QUIET_KINDS = frozenset(
    {"offers", "follow_up", "interview", "contact", "funding", "orp_target", "first_alert"}
)


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


PHONE_TOPIC = "phone_topic"


async def phone_settings(session: AsyncSession, settings: Settings) -> Settings | None:
    """Où envoyer sur le téléphone (docs/65 §4) : le sujet ntfy de l'installation pour
    l'exploitant ; pour un compte invité, le sien, s'il l'a activé. None : pas d'envoi."""
    if await accounts.is_owner(session):
        return settings if settings.ntfy_configured else None
    topic = await session.scalar(select(Setting.value).where(Setting.key == PHONE_TOPIC))
    if not topic:
        return None
    return settings.model_copy(update={"ntfy_topic": SecretStr(str(topic))})


def new_topic() -> str:
    """Un sujet tiré au hasard : qui le connaît lit les messages, il ne se devine pas."""
    return "jobbot-" + secrets.token_urlsafe(18)


# Remplaçable en test : aucun envoi réel.
send: Callable[[Settings, Message], Awaitable[None]] = http_send


async def deliver(
    runtime: Runtime, message: Message, *, kind: str, link: str, phone: Message | None = None
) -> None:
    """Une alerte : toujours dans la cloche (docs/15 §1), et sur le téléphone si ntfy est
    configuré, sauf un jour de repos pour ce qui peut attendre (docs/86). Un échec de
    ntfy n'empêche pas l'alerte d'être dans la cloche. `phone` : un autre texte pour le
    téléphone, quand la cloche peut en dire plus (le code d'un site, docs/120)."""
    async with runtime.sessionmaker.begin() as session:
        session.add(
            Notification(kind=kind, title=message.title, message=message.message, link=link)
        )
        target = await phone_settings(session, runtime.settings)
        if kind in QUIET_KINDS and not await rhythm.is_research_day(session):
            target = None
    if target is None:
        return
    try:
        await send(target, phone or message)
    except httpx.HTTPError as exc:
        log.warning("ntfy_send_failed", kind=kind, error=type(exc).__name__)


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
        lines.append(f"… et {plural(len(rows) - MAX_LISTED, 'autre', 'autres')}")
    best = rows[0][0]
    return Message(
        title=(
            f"{plural(len(rows), 'nouvelle offre', 'nouvelles offres')} pour toi"
            f" (jusqu'à {best}/100)"
        ),
        message="\n".join(lines),
        priority=4 if best >= 85 else 3,
        tags=["briefcase"],
        click=f"{settings.public_url.rstrip('/')}/candidatures/offres?tri=score",
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


async def _digest_due(runtime: Runtime, now: datetime) -> bool:
    """Le message du jour (docs/86) : un jour de recherche, dès l'heure choisie, une fois."""
    local = now.astimezone(LOCAL_TZ)
    async with runtime.sessionmaker() as session:
        settings = await rhythm.load(session)
        last = await session.scalar(select(Setting.value).where(Setting.key == DIGEST_KEY))
    if settings.mode == "instant":
        return True
    return (
        settings.research(local.date())
        and local.hour >= settings.hour
        and last != local.date().isoformat()
    )


async def notify_new_scores(runtime: Runtime, now: datetime | None = None) -> NotifyResult:
    settings = runtime.settings
    result = NotifyResult(configured=settings.ntfy_configured)
    threshold = await _threshold(runtime)
    moment = now or rhythm.now()
    due = await _digest_due(runtime, moment)
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
    if rows and due:
        await deliver(
            runtime,
            offers_message(settings, [(r[1] or 0, r[2], r[3], r[4]) for r in rows]),
            kind="offers",
            link="/candidatures/offres?tri=score",
        )
        async with runtime.sessionmaker.begin() as session:
            await session.execute(
                update(Evaluation)
                .where(Evaluation.id.in_([r[0] for r in rows]))
                .values(notified_at=datetime.now(UTC))
            )
            day = moment.astimezone(LOCAL_TZ).date().isoformat()
            await session.execute(
                insert(Setting)
                .values(key=DIGEST_KEY, value=day)
                .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": day})
            )
        result.offers = len(rows)

    # Les notes trop basses ne seront jamais signalées : on les marque aussi, pour ne
    # pas les signaler si le seuil baisse plus tard (seules les nouvelles notes comptent).
    # Les bonnes notes pas encore envoyées attendent le message du jour.
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Evaluation)
            .where(
                Evaluation.notified_at.is_(None),
                Evaluation.scored_at.is_not(None),
                or_(Evaluation.score.is_(None), Evaluation.score < threshold),
            )
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
    await deliver(
        runtime,
        Message(
            title="Budget de l'IA presque atteint",
            message=f"{spend:.2f} CHF dépensés sur {budget:.2f} CHF ce mois-ci. "
            "Au-delà du plafond, les offres ne sont plus notées jusqu'au mois prochain.",
            priority=4,
            tags=["warning"],
            click=f"{runtime.settings.public_url.rstrip('/')}/reglages",
        ),
        kind="budget",
        link="/reglages",
    )
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            insert(Setting)
            .values(key=BUDGET_ALERT_KEY, value=month)
            .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": month})
        )
    return True


async def send_test(settings: Settings) -> None:
    await send(
        settings,
        Message(
            title="jobA1 : notification de test",
            message="Les notifications fonctionnent. Tu seras prévenu des offres bien notées.",
            tags=["white_check_mark"],
            click=f"{settings.public_url.rstrip('/')}/candidatures/offres",
        ),
    )


# --- Relances (0.5) -------------------------------------------------------------------


async def notify_reminders(runtime: Runtime, today: date | None = None) -> int:
    """Candidatures en attente depuis 10 jours : une alerte groupée, une seule fois par
    candidature (cloche, et téléphone si ntfy est configuré)."""
    settings = runtime.settings
    today = today or datetime.now(UTC).date()
    async with runtime.sessionmaker() as session:
        due = list(
            await session.scalars(
                select(Application)
                .where(Application.reminded_at.is_(None), remind_due(today))
                .order_by(Application.sent_at)
            )
        )
    if not due:
        return 0
    lines = [
        f"{a.company} — {a.job_title} (envoyée le {a.sent_at:%d.%m})" for a in due[:MAX_LISTED]
    ]
    if len(due) > MAX_LISTED:
        lines.append(f"… et {plural(len(due) - MAX_LISTED, 'autre', 'autres')}")
    await deliver(
        runtime,
        Message(
            title=(
                f"{plural(len(due), 'candidature', 'candidatures')} sans réponse"
                f" depuis {REMIND_AFTER_DAYS} jours"
            ),
            message="Relancer ?\n" + "\n".join(lines),
            tags=["hourglass"],
            click=f"{settings.public_url.rstrip('/')}/candidatures/suivi",
        ),
        kind="follow_up",
        link="/candidatures/suivi",
    )
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Application)
            .where(Application.id.in_([a.id for a in due]))
            .values(reminded_at=datetime.now(UTC))
        )
    log.info("reminders_sent", applications=len(due))
    return len(due)
