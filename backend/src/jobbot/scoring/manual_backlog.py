"""Note des anciennes offres ajoutées à la main et jamais notées, sur demande (décision de
Kevin du 2026-11-15).

Depuis MANUAL_SCORED_SINCE, une offre ajoutée à la main est notée quel que soit son statut.
Celles d'avant (dont la 726, ajoutée puis écartée par les critères) ne sont pas reprises par la
tâche des 10 minutes : `jobbot noter-offres-manuelles` les compte, par compte, avec le coût
estimé ; `--lancer` les note, puis dit combien sont notées, en échec, et les jetons consommés.

Idempotente : seules les offres ajoutées à la main dont la note est vide sont prises ; une
fois notées, une seconde exécution n'en trouve plus. Rien n'est noté sans `--lancer`.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts
from jobbot.db.models import MANUAL_LINK_SOURCE, Evaluation, LlmCall, Offer, OfferLink
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.scoring import service

log = get_logger(__name__)


@dataclass
class Found:
    account: int
    offers: int
    cost_chf: Decimal


@dataclass
class Done:
    scored: int = 0
    failed: int = 0
    skipped: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_chf: Decimal = Decimal(0)
    budget_reached: bool = False
    limit_reached: bool = False
    accounts: list[int] = field(default_factory=list)


async def pending(session: AsyncSession) -> list[Offer]:
    """Les offres du compte en cours ajoutées à la main, encore là, dont la note est vide."""
    manual = select(OfferLink.offer_id).where(
        OfferLink.offer_id == Offer.id, OfferLink.source == MANUAL_LINK_SOURCE
    )
    rows = await session.scalars(
        select(Offer)
        .outerjoin(Evaluation, Evaluation.offer_id == Offer.id)
        .where(
            manual.exists(),
            Offer.expired_at.is_(None),
            Offer.duplicate_of.is_(None),
            Offer.spontaneous.is_(False),
            or_(Evaluation.id.is_(None), Evaluation.score.is_(None)),
        )
        .order_by(Offer.id)
    )
    return list(rows)


async def _accounts(runtime: Runtime, only: int | None) -> list[int]:
    async with runtime.sessionmaker() as session:
        everyone = await accounts.account_ids(session)
    return [a for a in everyone if only is None or a == only]


async def count(runtime: Runtime, only: int | None = None) -> list[Found]:
    """Le nombre d'offres à noter et le coût estimé, par compte. Aucun appel à l'IA."""
    found: list[Found] = []
    for account in await _accounts(runtime, only):
        with accounts.use(account):
            async with runtime.sessionmaker() as session:
                offers = await pending(session)
                _, _, rate = await service.budget_state(session, datetime.now(UTC))
        if offers:
            cost = (len(offers) * service.ESTIMATE_USD * rate).quantize(Decimal("0.01"))
            found.append(Found(account=account, offers=len(offers), cost_chf=cost))
    return found


async def score_all(runtime: Runtime, only: int | None = None) -> Done:
    """Note les offres trouvées par `count`, compte par compte, dans les limites du plafond et
    de la formule. Rend le bilan (notées, en échec, jetons)."""
    done = Done()
    # L'heure de la base, pour ne compter que les appels de cette exécution.
    async with runtime.sessionmaker() as session:
        started = await session.scalar(select(func.now()))
    client = service.make_client(runtime.settings)
    for account in await _accounts(runtime, only):
        with accounts.use(account):
            async with runtime.sessionmaker() as session:
                offers = await pending(session)
                if not offers:
                    continue
                profile = await service.active_profile(session)
                allowed, limited = await service.within_plan(session, offers)
            done.accounts.append(account)
            done.skipped += len(offers) - len(allowed)
            done.limit_reached |= limited
            result = service.ScoringResult()
            await service._score_direct(runtime, client, allowed, profile, result)
            done.scored += result.scored
            done.failed += result.failed
            done.budget_reached |= result.budget_reached
            # Une offre arrêtée en route (plafond, API injoignable) n'est ni notée ni en échec.
            done.skipped += len(allowed) - result.scored - result.failed
            async with runtime.sessionmaker() as session:
                used = (
                    await session.execute(
                        select(
                            func.coalesce(
                                func.sum(
                                    LlmCall.input_tokens
                                    + LlmCall.cache_read_tokens
                                    + LlmCall.cache_write_tokens
                                ),
                                0,
                            ),
                            func.coalesce(func.sum(LlmCall.output_tokens), 0),
                            func.coalesce(func.sum(LlmCall.cost_chf), 0),
                        ).where(
                            LlmCall.purpose == "score",
                            LlmCall.created_at >= started,
                            LlmCall.offer_id.in_([o.id for o in allowed] or [0]),
                        )
                    )
                ).one()
            done.input_tokens += int(used[0])
            done.output_tokens += int(used[1])
            done.cost_chf += Decimal(used[2])
    log.info(
        "manual_backlog_scored",
        scored=done.scored,
        failed=done.failed,
        skipped=done.skipped,
        input_tokens=done.input_tokens,
        output_tokens=done.output_tokens,
        cost_chf=str(done.cost_chf),
    )
    return done
