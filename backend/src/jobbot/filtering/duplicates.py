"""Doublons et ancienneté des annonces (docs/30 §2), sans IA.

Deux offres au même titre et à la même entreprise (autre site, autre lien) sont la même
annonce : la plus avancée (envoyée, en préparation, mise de côté…) ou à défaut la plus récente
est gardée, les autres lui sont rattachées et disparaissent des listes. `seen_since` garde la
première apparition de l'annonce, doublons compris : au-delà de 30 jours, c'est une annonce
permanente.
"""

from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_text
from jobbot.db.models import Offer, OfferStatus

# L'offre gardée dans un groupe : celle sur laquelle tu as agi, puis une offre en ligne.
RANK: dict[str, int] = {
    OfferStatus.APPLIED: 5,
    OfferStatus.PREPARING: 4,
    OfferStatus.LATER: 3,
    OfferStatus.TO_REVIEW: 2,
    OfferStatus.NEW: 2,
    OfferStatus.FILTERED_OUT: 1,
    OfferStatus.IGNORED: 0,
}


def _key(offer: Offer) -> tuple[str, str] | None:
    title, company = normalize_text(offer.title), normalize_text(offer.company or "")
    return (title, company) if title and company else None


def _keep(group: list[Offer]) -> Offer:
    return max(
        group,
        key=lambda o: (RANK.get(o.status, 0), o.expired_at is None, o.first_seen_at, o.id),
    )


async def group_duplicates(session: AsyncSession) -> int:
    """Rattache les doublons à l'offre gardée ; rend le nombre d'offres rattachées."""
    groups: dict[tuple[str, str], list[Offer]] = defaultdict(list)
    alone: list[Offer] = []
    # Une candidature spontanée n'est le doublon de rien (docs/39 §4).
    for offer in await session.scalars(select(Offer).where(Offer.spontaneous.is_(False))):
        key = _key(offer)
        if key is None:
            alone.append(offer)
        else:
            groups[key].append(offer)
    attached = 0
    for group in groups.values():
        kept = _keep(group)
        first: datetime = min(o.first_seen_at for o in group)
        for offer in group:
            if offer is kept:
                offer.duplicate_of = None
                offer.seen_since = first
            else:
                offer.duplicate_of = kept.id
                offer.seen_since = offer.first_seen_at
                attached += 1
    for offer in alone:
        offer.duplicate_of = None
        offer.seen_since = offer.seen_since or offer.first_seen_at
    return attached
