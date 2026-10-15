"""Demande de financement d'une formation à l'ORP (docs/37 §2).

Sans IA : l'argument vient de tes offres (celles des 90 derniers jours dont les exigences
contiennent un mot-clé de la formation). Rien n'est envoyé : tu copies le texte. Un rappel
arrive 14 jours après une demande restée sans réponse, une seule fois.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import Evaluation, Offer, Profile, Training, TrainingMark
from jobbot.news import domain
from jobbot.notify.service import Message, deliver
from jobbot.runtime import Runtime

WINDOW = timedelta(days=90)
FOLLOW_UP_AFTER = timedelta(days=14)
EXAMPLES = 3
MATCHED = 3
# Au plus tant d'offres lues pour l'argument (les plus récentes).
SCAN_LIMIT = 1_000


@dataclass(frozen=True)
class Example:
    title: str
    company: str | None


@dataclass(frozen=True)
class Argument:
    offers: int
    # Mots-clés de la formation les plus demandés, dans l'ordre de fréquence.
    matched: list[str]
    examples: list[Example]


def _asks(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [a["text"] for a in value if isinstance(a, dict) and isinstance(a.get("text"), str)]


async def argument(
    session: AsyncSession, training: Training, now: datetime | None = None
) -> Argument:
    """Les offres récentes qui demandent ce que la formation apporte."""
    tags = [t for t in training.tags if isinstance(t, str)]
    if not tags:
        return Argument(0, [], [])
    since = (now or datetime.now(UTC)) - WINDOW
    rows = (
        await session.execute(
            select(Offer.title, Offer.company, Evaluation.keywords_asks)
            .join(Evaluation, Evaluation.offer_id == Offer.id)
            .where(Offer.first_seen_at >= since, Offer.duplicate_of.is_(None))
            .order_by(Offer.first_seen_at.desc(), Offer.id.desc())
            .limit(SCAN_LIMIT)
        )
    ).all()
    count = 0
    seen: Counter[str] = Counter()
    examples: list[Example] = []
    for title, company, asks in rows:
        found = domain.matched(tags, *_asks(asks))
        if not found:
            continue
        count += 1
        seen.update(found)
        if len(examples) < EXAMPLES:
            examples.append(Example(title, company))
    return Argument(count, [tag for tag, _ in seen.most_common(MATCHED)], examples)


def local_today() -> date:
    return datetime.now(UTC).astimezone(LOCAL_TZ).date()


async def due(session: AsyncSession, today: date | None = None) -> list[tuple[TrainingMark, str]]:
    """Demandes sans réponse depuis 14 jours, pas encore rappelées."""
    limit = (today or local_today()) - FOLLOW_UP_AFTER
    rows = await session.execute(
        select(TrainingMark, Training.title)
        .join(Training, Training.id == TrainingMark.training_id)
        # Le lien du rappel ouvre le profil principal : ses demandes seulement.
        .join(Profile, Profile.id == TrainingMark.profile_id)
        .where(
            Profile.is_main.is_(True),
            TrainingMark.funding_status == "requested",
            TrainingMark.funding_requested_at <= limit,
            TrainingMark.funding_reminded_at.is_(None),
        )
    )
    return [(mark, title) for mark, title in rows.all()]


async def notify_funding(runtime: Runtime) -> int:
    """Un rappel par demande de financement restée sans réponse, une seule fois."""
    async with runtime.sessionmaker() as session:
        pending = [(m.profile_id, m.training_id, title) for m, title in await due(session)]
    for profile_id, training_id, title in pending:
        await deliver(
            runtime,
            Message(
                title=f"Relancer ton conseiller ORP pour « {title} » ?",
                message="Pas de réponse depuis deux semaines à ta demande de financement.",
                tags=["mortar_board"],
            ),
            kind="training_funding",
            link="/formations?onglet=miennes",
        )
        async with runtime.sessionmaker.begin() as session:
            mark = await session.get(TrainingMark, (profile_id, training_id))
            if mark is not None:
                mark.funding_reminded_at = datetime.now(UTC)
    return len(pending)
