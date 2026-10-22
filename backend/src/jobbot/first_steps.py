"""Les premiers pas (docs/128 §1) : cinq étapes, une seule prochaine action sur Aujourd'hui.

Chaque étape se lit dans ce qui existe déjà. Une étape faite le reste : une étape plus loin
coche celles d'avant, et la plus haute atteinte est gardée dans `first_steps_reached`, si bien
qu'une offre gardée puis écartée laisse l'étape 3 faite. La fonction SQL
`first_steps_progress` (migration 0070) applique les mêmes règles pour le chiffre de l'équipe.
"""

from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.base import READ_ONLY
from jobbot.db.models import (
    AlertSetup,
    Application,
    Criterion,
    Document,
    Draft,
    Offer,
    OfferStatus,
    Search,
    Setting,
)

StepKey = Literal["profile", "alerts", "keep", "prepare", "sent"]
STEPS: tuple[StepKey, ...] = ("profile", "alerts", "keep", "prepare", "sent")
REACHED_KEY = "first_steps_reached"
DISMISSED_KEY = "first_steps_dismissed"
# La carte de réussite a été montrée (l'interface le dit) ; d'office pour un compte qui avait
# déjà tout fait avant la 1.1.0.
CELEBRATED_KEY = "first_steps_celebrated"
KEPT = (OfferStatus.PREPARING, OfferStatus.APPLIED)


@dataclass(frozen=True)
class FirstSteps:
    # Le nombre d'étapes faites (0 à 5) : les premières de la liste.
    reached: int
    dismissed: bool
    # Une offre visible existe (sinon, alertes créées : on attend les premières).
    has_offers: bool
    # L'offre à préparer pour les étapes 4 et 5 : la dernière gardée.
    offer_id: int | None
    # Les cinq étapes sont faites et la réussite n'a pas encore été montrée.
    just_finished: bool


async def _found(session: AsyncSession, query: Select[Any]) -> bool:
    return bool(await session.scalar(select(query.exists())))


async def _computed(session: AsyncSession) -> int:
    """La plus haute étape faite d'après les données, en nombre d'étapes (0 à 5)."""
    rules = (
        await _found(session, select(Criterion.kind))
        and await _found(session, select(Document.id)),
        await _found(session, select(AlertSetup.search_id))
        or await _found(session, select(Search.id))
        or await _found(session, select(Offer.id)),
        await _found(session, select(Offer.id).where(Offer.status.in_(KEPT))),
        await _found(session, select(Draft.id)),
        await _found(session, select(Application.id)),
    )
    return max((i + 1 for i, done in enumerate(rules) if done), default=0)


async def _setting(session: AsyncSession, key: str, value: object) -> None:
    await session.execute(
        insert(Setting)
        .values(key=key, value=value)
        .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": value})
    )


async def load(session: AsyncSession) -> FirstSteps:
    """Lit les étapes, garde la plus haute atteinte (la session doit pouvoir écrire)."""
    values = {
        s.key: s.value
        for s in await session.scalars(
            select(Setting).where(Setting.key.in_((REACHED_KEY, DISMISSED_KEY, CELEBRATED_KEY)))
        )
    }
    stored = values.get(REACHED_KEY)
    known = int(stored) if isinstance(stored, int) else None
    reached = max(await _computed(session), known or 0)
    # Un compte qui avait déjà tout fait avant la 1.1.0 (la démo aussi) ne voit pas la réussite.
    celebrated = bool(values.get(CELEBRATED_KEY)) or (known is None and reached == len(STEPS))
    # La démo est en lecture seule (docs/76 §1) : elle lit les étapes sans rien garder.
    if not READ_ONLY.get():
        if known is None or reached > known:
            await _setting(session, REACHED_KEY, reached)
        if celebrated and not values.get(CELEBRATED_KEY):
            await _setting(session, CELEBRATED_KEY, True)
    has_offers = await _found(
        session, select(Offer.id).where(Offer.status != OfferStatus.FILTERED_OUT)
    )
    # La dernière offre préparée (une lettre ou un CV), sinon la dernière gardée.
    offer_id = await session.scalar(
        select(Draft.offer_id)
        .join(Offer, Offer.id == Draft.offer_id)
        .where(Offer.status == OfferStatus.PREPARING)
        .order_by(Draft.created_at.desc())
        .limit(1)
    ) or await session.scalar(
        select(func.max(Offer.id)).where(Offer.status == OfferStatus.PREPARING)
    )
    return FirstSteps(
        reached=reached,
        dismissed=bool(values.get(DISMISSED_KEY)),
        has_offers=has_offers,
        offer_id=offer_id,
        just_finished=reached == len(STEPS) and not celebrated,
    )


async def dismiss(session: AsyncSession, dismissed: bool) -> None:
    await _setting(session, DISMISSED_KEY, dismissed)


async def celebrate(session: AsyncSession) -> None:
    """La carte de réussite a été montrée : elle ne revient plus."""
    await _setting(session, CELEBRATED_KEY, True)
