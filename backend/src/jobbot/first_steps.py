"""Les premiers pas (docs/128 §1) : cinq étapes, une seule prochaine action sur Aujourd'hui.

Chaque étape se lit dans ce qui existe déjà. Une étape faite le reste : une étape plus loin
coche celles d'avant, et la plus haute atteinte est gardée dans `first_steps_reached`, si bien
qu'une offre gardée puis écartée laisse l'étape 3 faite. La fonction SQL
`first_steps_progress` (migration 0070, règle des alertes revue en 0084) applique les mêmes
règles pour le chiffre de l'équipe.

L'étape des alertes fait exception (corrections du 13.11 au soir, §1, décision de Kevin du
14.11) : elle n'est faite qu'avec une alerte créée (« J'ai créé l'alerte ») ou reçue, jamais par
les offres de la recherche publique. Après « Plus tard », elle reste ouverte sur la carte même si
une étape plus loin est faite, jusqu'à la première candidature envoyée.
"""

from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import welcome
from jobbot.alerts.service import is_canton
from jobbot.db.base import READ_ONLY
from jobbot.db.models import (
    AlertSetup,
    Application,
    ChunkKind,
    Criterion,
    Document,
    Draft,
    Offer,
    OfferStatus,
    ProfileChunk,
    Search,
    Setting,
    received_alert,
)

StepKey = Literal["profile", "alerts", "keep", "prepare", "sent"]
STEPS: tuple[StepKey, ...] = ("profile", "alerts", "keep", "prepare", "sent")
# Les cinq lignes d'Aujourd'hui (§22 du 15.11, option B de Kevin) : le CV et les critères
# séparés, « préparer » et « envoyer » réunis. Les étapes gardées (STEPS, `first_steps_reached`,
# la fonction SQL, l'API des partenaires) ne changent pas : les lignes s'en déduisent.
RowKey = Literal["cv", "criteria", "alerts", "keep", "send"]
REACHED_KEY = "first_steps_reached"
DISMISSED_KEY = "first_steps_dismissed"
# La carte de réussite a été montrée (l'interface le dit) ; d'office pour un compte qui avait
# déjà tout fait avant la 1.1.0.
CELEBRATED_KEY = "first_steps_celebrated"
KEPT = (OfferStatus.PREPARING, OfferStatus.APPLIED)


@dataclass(frozen=True)
class Summary:
    """Les sous-titres des lignes faites : « 12 compétences reprises », « DevOps · Lausanne ·
    80 à 100 % ». Le métier tel que la personne l'a écrit à l'accueil, le premier lieu qui n'est
    pas un canton, le taux minimum des critères, le nombre d'offres gardées (« 3 offres
    gardées », Kevin le 16.11)."""

    skills: int
    trade: str | None
    place: str | None
    min_rate: int | None
    kept: int = 0


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
    # Une alerte créée ou reçue (l'étape des alertes, qui ne se coche pas autrement).
    alerts_done: bool = True
    # Un CV déposé, des critères enregistrés : les deux moitiés de l'étape 1.
    cv_done: bool = False
    criteria_done: bool = False

    def rows(self) -> list[tuple[RowKey, bool]]:
        """Les cinq lignes d'Aujourd'hui, faites ou non."""
        first = self.done(0)
        return [
            ("cv", first or self.cv_done),
            ("criteria", first or self.criteria_done),
            ("alerts", self.done(1)),
            ("keep", self.done(2)),
            ("send", self.done(4)),
        ]

    def done(self, index: int) -> bool:
        """L'étape `index` (0 à 4) est faite : les `reached` premières, sauf les alertes tant
        qu'aucune n'est créée ni reçue, et qu'aucune candidature n'est partie."""
        if STEPS[index] == "alerts" and not self.alerts_done and self.reached < len(STEPS):
            return False
        return index < self.reached


async def _found(session: AsyncSession, query: Select[Any]) -> bool:
    return bool(await session.scalar(select(query.exists())))


async def _alerts(session: AsyncSession) -> bool:
    """Une alerte créée (« J'ai créé l'alerte ») ou reçue ; ni la recherche publique, ni un code
    ou un message d'un site (docs/112), ni une offre."""
    return await _found(session, select(AlertSetup.search_id)) or await _found(
        session, select(Search.id).where(received_alert())
    )


async def _computed(session: AsyncSession) -> int:
    """La plus haute étape faite d'après les données, en nombre d'étapes (0 à 5)."""
    rules = (
        await _found(session, select(Criterion.kind))
        and await _found(session, select(Document.id)),
        await _alerts(session),
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


async def reached(session: AsyncSession) -> int:
    """Le nombre d'étapes faites, sans rien garder : pour une lecture d'une app partenaire
    (docs/140 §3), qui ne doit pas changer ce que la personne verra dans jobA1."""
    stored = await session.scalar(select(Setting.value).where(Setting.key == REACHED_KEY))
    return max(await _computed(session), stored if isinstance(stored, int) else 0)


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
    alerts_done = await _alerts(session)
    return FirstSteps(
        cv_done=await _found(session, select(Document.id)),
        criteria_done=await _found(session, select(Criterion.kind)),
        reached=reached,
        dismissed=bool(values.get(DISMISSED_KEY)),
        has_offers=has_offers,
        offer_id=offer_id,
        just_finished=reached == len(STEPS) and not celebrated,
        alerts_done=alerts_done,
    )


async def summary(session: AsyncSession) -> Summary:
    skills = await session.scalar(
        select(func.count())
        .select_from(ProfileChunk)
        .where(ProfileChunk.kind == ChunkKind.COMPETENCE, ProfileChunk.active.is_(True))
    )
    trade = (await welcome.state(session)).get("trade")
    rows = {c.kind: c.value for c in await session.scalars(select(Criterion))}
    locations = [v for v in rows.get("locations") or [] if isinstance(v, str)]
    places = [v for v in locations if not is_canton(v)]
    rate = rows.get("min_rate")
    kept = await session.scalar(
        select(func.count()).select_from(Offer).where(Offer.status.in_(KEPT))
    )
    return Summary(
        skills=skills or 0,
        trade=trade.strip() or None if isinstance(trade, str) else None,
        place=places[0] if places else None,
        min_rate=rate if isinstance(rate, int) else None,
        kept=kept or 0,
    )


async def dismiss(session: AsyncSession, dismissed: bool) -> None:
    await _setting(session, DISMISSED_KEY, dismissed)


async def celebrate(session: AsyncSession) -> None:
    """La carte de réussite a été montrée : elle ne revient plus."""
    await _setting(session, CELEBRATED_KEY, True)
