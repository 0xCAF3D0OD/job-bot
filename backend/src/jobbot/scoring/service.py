"""Note et résumé des offres par l'IA (docs/06-note-ia.md).

- Nouvelles offres (peu nombreuses) : appels directs, quelques secondes chacun.
- Rattrapage ou renotation (nombreuses) : un lot, à moitié prix, relevé plus tard.
- Plafond mensuel en CHF : plus aucun appel une fois atteint.
- Seules les offres à examiner sont notées, jamais les écartées.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import anthropic
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import (
    Evaluation,
    LlmBatch,
    LlmCall,
    Offer,
    OfferStatus,
    ProfileChunk,
    Setting,
)
from jobbot.llm.client import BatchItem, RawResult, Refused, ScoreClient, client_factory
from jobbot.llm.pricing import cost_usd
from jobbot.llm.scoring import (
    PROMPT_VERSION,
    InvalidScore,
    OfferData,
    ProfileChunkData,
    ScoreOutput,
    parse_output,
    profile_hash,
    request_params,
)
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.settings import Settings

log = get_logger(__name__)

# Au-delà de ce nombre d'offres à noter d'un coup, on passe par un lot.
DIRECT_LIMIT = 20
# Estimation prudente du coût d'une note, pour ne pas dépasser le plafond (docs/06 §3).
ESTIMATE_USD = Decimal("0.03")
TO_SCORE = (OfferStatus.NEW, OfferStatus.TO_REVIEW)

# Remplaçable en test par un faux client.
make_client = client_factory


class ScoringUnavailable(Exception):
    """Problème du compte API (clé refusée, crédit épuisé) : rien ne sert de continuer, et ce
    n'est pas la faute des offres, qui restent à noter."""


def account_problem(exc: anthropic.APIStatusError) -> str | None:
    if isinstance(exc, anthropic.AuthenticationError | anthropic.PermissionDeniedError):
        return "clé API Anthropic refusée : vérifier JOBBOT_ANTHROPIC_API_KEY"
    if "credit balance" in str(exc.message).lower():
        return "crédit API Anthropic épuisé : en racheter dans la console (Plans & Billing)"
    return None


@dataclass
class ScoringResult:
    configured: bool = True
    scored: int = 0
    failed: int = 0
    batch_submitted: int = 0
    batch_collected: int = 0
    budget_reached: bool = False


# --- Lecture ----------------------------------------------------------------------------


async def active_profile(session: AsyncSession) -> list[ProfileChunkData]:
    rows = await session.scalars(
        select(ProfileChunk).where(ProfileChunk.active.is_(True)).order_by(ProfileChunk.id)
    )
    return [ProfileChunkData(c.id, c.kind, c.title, c.content) for c in rows]


async def _setting(session: AsyncSession, key: str, default: Decimal) -> Decimal:
    value = await session.scalar(select(Setting.value).where(Setting.key == key))
    return Decimal(str(value)) if value is not None else default


async def month_spend_chf(session: AsyncSession, now: datetime) -> Decimal:
    start = now.astimezone(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total = await session.scalar(
        select(func.coalesce(func.sum(LlmCall.cost_chf), 0)).where(LlmCall.created_at >= start)
    )
    return Decimal(str(total))


async def budget_state(session: AsyncSession, now: datetime) -> tuple[Decimal, Decimal, Decimal]:
    """(dépense du mois en CHF, plafond en CHF, taux USD→CHF)."""
    spend = await month_spend_chf(session, now)
    budget = await _setting(session, "llm_monthly_budget_chf", Decimal("10"))
    rate = await _setting(session, "usd_chf_rate", Decimal("0.8"))
    return spend, budget, rate


def _rate_text(offer: Offer) -> str | None:
    if offer.rate_min is None or offer.rate_max is None:
        return None
    if offer.rate_min == offer.rate_max:
        return f"{offer.rate_min} %"
    return f"{offer.rate_min}-{offer.rate_max} %"


def offer_data(offer: Offer) -> OfferData:
    return OfferData(
        id=offer.id,
        title=offer.title,
        company=offer.company,
        location=offer.location,
        rate=_rate_text(offer),
        employment_type=offer.employment_type,
        text=offer.description or offer.snippet,
        partial=offer.description is None,
    )


async def _pending_batch_offers(session: AsyncSession) -> set[int]:
    rows = await session.scalars(select(LlmBatch.offer_ids).where(LlmBatch.status == "in_progress"))
    return {offer_id for ids in rows for offer_id in ids}


async def candidates(
    session: AsyncSession, current_hash: str, *, include_stale_profile: bool
) -> list[Offer]:
    """Offres à examiner sans note à jour (jamais notées, consignes changées, ou texte
    complet arrivé après une note faite sur l'extrait). Avec `include_stale_profile`,
    aussi celles notées avec un autre profil (renotation sur clic de Kevin)."""
    needs = [
        Evaluation.id.is_(None),
        and_(Evaluation.scored_at.is_(None), Evaluation.score_error.is_(None)),
        Evaluation.prompt_version != PROMPT_VERSION,
        and_(Offer.description.is_not(None), Evaluation.summary_partial.is_(True)),
    ]
    if include_stale_profile:
        needs.append(Evaluation.profile_hash != current_hash)
        needs.append(Evaluation.score_error.is_not(None))
    rows = await session.scalars(
        select(Offer)
        .outerjoin(Evaluation, Evaluation.offer_id == Offer.id)
        .where(Offer.status.in_(TO_SCORE), or_(*needs))
        .order_by(Offer.first_seen_at.desc(), Offer.id.desc())
    )
    pending = await _pending_batch_offers(session)
    return [offer for offer in rows if offer.id not in pending]


# --- Écriture ---------------------------------------------------------------------------


async def _store(
    session: AsyncSession,
    offer_id: int,
    *,
    output: ScoreOutput | None,
    model: str,
    hash_: str,
    partial: bool,
    error: str | None = None,
) -> None:
    now = datetime.now(UTC)
    values: dict[str, Any] = {
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "profile_hash": hash_,
        "score_error": error,
    }
    if output is not None:
        values |= {
            "score": output.score,
            "summary_role": output.summary_role,
            "summary_asks": output.summary_asks,
            "summary_offers": output.summary_offers,
            "summary_partial": partial,
            "strengths": [p.model_dump() for p in output.strengths],
            "gaps": [p.model_dump() for p in output.gaps],
            "scored_at": now,
        }
    # Une offre pas encore passée par le filtre n'a pas de ligne : on la crée, le filtre
    # complétera ses colonnes.
    await session.execute(
        insert(Evaluation)
        .values(
            offer_id=offer_id, filter_passed=True, filter_reasons=[], criteria_hash="", **values
        )
        .on_conflict_do_update(index_elements=["offer_id"], set_=values)
    )


async def record_call(
    session: AsyncSession,
    raw: RawResult,
    *,
    offer_id: int | None,
    rate: Decimal,
    batch_id: str | None = None,
    purpose: str = "score",
) -> Decimal:
    usd = cost_usd(raw.model, raw.usage, batch=batch_id is not None)
    chf = (usd * rate).quantize(Decimal("0.00001"))
    session.add(
        LlmCall(
            purpose=purpose,
            offer_id=offer_id,
            model=raw.model,
            batch_id=batch_id,
            input_tokens=raw.usage.input_tokens,
            cache_read_tokens=raw.usage.cache_read_tokens,
            cache_write_tokens=raw.usage.cache_write_tokens,
            output_tokens=raw.usage.output_tokens,
            cost_usd=usd,
            cost_chf=chf,
        )
    )
    return chf


# --- Lots -------------------------------------------------------------------------------


def _offer_id(custom_id: str) -> int | None:
    prefix, _, value = custom_id.partition("-")
    return int(value) if prefix == "offre" and value.isdigit() else None


async def collect_batches(runtime: Runtime, client: ScoreClient, result: ScoringResult) -> None:
    async with runtime.sessionmaker() as session:
        pending = list(
            await session.scalars(select(LlmBatch).where(LlmBatch.status == "in_progress"))
        )
    for batch in pending:
        if not await client.batch_ended(batch.provider_batch_id):
            continue
        async with runtime.sessionmaker.begin() as session:
            profile = await active_profile(session)
            hash_ = profile_hash(profile)
            _, _, rate = await budget_state(session, datetime.now(UTC))
            offers = {
                o.id: o
                for o in await session.scalars(select(Offer).where(Offer.id.in_(batch.offer_ids)))
            }
            item: BatchItem
            async for item in client.batch_results(batch.provider_batch_id):
                offer_id = _offer_id(item.custom_id)
                offer = offers.get(offer_id) if offer_id is not None else None
                if offer is None:
                    continue
                partial = offer.description is None
                if item.result is None:
                    await _store(
                        session,
                        offer.id,
                        output=None,
                        model=runtime.settings.llm_model,
                        hash_=hash_,
                        partial=partial,
                        error=f"lot : {item.error}",
                    )
                    result.failed += 1
                    continue
                await record_call(
                    session,
                    item.result,
                    offer_id=offer.id,
                    rate=rate,
                    batch_id=batch.provider_batch_id,
                )
                try:
                    output = parse_output(item.result.text, profile)
                except InvalidScore as exc:
                    await _store(
                        session,
                        offer.id,
                        output=None,
                        model=item.result.model,
                        hash_=hash_,
                        partial=partial,
                        error=str(exc),
                    )
                    result.failed += 1
                    continue
                await _store(
                    session,
                    offer.id,
                    output=output,
                    model=item.result.model,
                    hash_=hash_,
                    partial=partial,
                )
                result.batch_collected += 1
            await session.execute(
                update(LlmBatch)
                .where(LlmBatch.id == batch.id)
                .values(status="ended", ended_at=datetime.now(UTC))
            )
        log.info("score_batch_collected", batch_id=batch.provider_batch_id)


async def _submit_batch(
    runtime: Runtime,
    client: ScoreClient,
    offers: list[Offer],
    profile: list[ProfileChunkData],
    result: ScoringResult,
) -> None:
    settings = runtime.settings
    requests = [
        (
            f"offre-{offer.id}",
            request_params(settings.llm_model, settings.llm_effort, profile, offer_data(offer)),
        )
        for offer in offers
    ]
    try:
        batch_id = await client.create_batch(requests)
    except anthropic.APIStatusError as exc:
        if problem := account_problem(exc):
            raise ScoringUnavailable(problem) from None
        raise
    async with runtime.sessionmaker.begin() as session:
        session.add(LlmBatch(provider_batch_id=batch_id, offer_ids=[o.id for o in offers]))
    result.batch_submitted += len(offers)
    log.info("score_batch_submitted", batch_id=batch_id, offers=len(offers))


# --- Appels directs ---------------------------------------------------------------------


async def _score_direct(
    runtime: Runtime,
    client: ScoreClient,
    offers: list[Offer],
    profile: list[ProfileChunkData],
    result: ScoringResult,
) -> None:
    settings = runtime.settings
    hash_ = profile_hash(profile)
    for offer in offers:
        async with runtime.sessionmaker.begin() as session:
            spend, budget, rate = await budget_state(session, datetime.now(UTC))
            if spend + ESTIMATE_USD * rate > budget:
                result.budget_reached = True
                log.warning("score_budget_reached", spend_chf=str(spend), budget_chf=str(budget))
                return
        data = offer_data(offer)
        params = request_params(settings.llm_model, settings.llm_effort, profile, data)
        try:
            raw = await client.score(params)
        except Refused as exc:
            error, raw = str(exc), None
        except (anthropic.RateLimitError, anthropic.APIConnectionError) as exc:
            log.warning("score_api_unavailable", error=type(exc).__name__)
            return  # nouvel essai à la prochaine exécution
        except anthropic.APIStatusError as exc:
            if problem := account_problem(exc):
                raise ScoringUnavailable(problem) from None
            error, raw = f"API : erreur {exc.status_code}", None

        async with runtime.sessionmaker.begin() as session:
            if raw is None:
                await _store(
                    session,
                    offer.id,
                    output=None,
                    model=settings.llm_model,
                    hash_=hash_,
                    partial=data.partial,
                    error=error,
                )
                result.failed += 1
                continue
            await record_call(session, raw, offer_id=offer.id, rate=rate)
            try:
                output = parse_output(raw.text, profile)
            except InvalidScore as exc:
                await _store(
                    session,
                    offer.id,
                    output=None,
                    model=raw.model,
                    hash_=hash_,
                    partial=data.partial,
                    error=str(exc),
                )
                result.failed += 1
                continue
            await _store(
                session, offer.id, output=output, model=raw.model, hash_=hash_, partial=data.partial
            )
            result.scored += 1


# --- Point d'entrée ---------------------------------------------------------------------


def _affordable(count: int, spend: Decimal, budget: Decimal, rate: Decimal, batch: bool) -> int:
    unit = ESTIMATE_USD * rate / (2 if batch else 1)
    if unit <= 0:
        return count
    return max(0, min(count, int((budget - spend) / unit)))


async def run_scoring(runtime: Runtime, *, rescore_profile: bool = False) -> ScoringResult:
    settings: Settings = runtime.settings
    if not settings.llm_configured:
        log.info("score_not_configured")
        return ScoringResult(configured=False)
    client = make_client(settings)
    result = ScoringResult()

    await collect_batches(runtime, client, result)

    async with runtime.sessionmaker() as session:
        profile = await active_profile(session)
        todo = await candidates(
            session, profile_hash(profile), include_stale_profile=rescore_profile
        )
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if not todo:
        return result

    use_batch = rescore_profile or len(todo) > DIRECT_LIMIT
    if use_batch:
        affordable = _affordable(len(todo), spend, budget, rate, batch=True)
        if affordable < len(todo):
            result.budget_reached = True
        if affordable:
            await _submit_batch(runtime, client, todo[:affordable], profile, result)
    else:
        await _score_direct(runtime, client, todo, profile, result)
    log.info(
        "score_finished",
        scored=result.scored,
        failed=result.failed,
        batch_submitted=result.batch_submitted,
        batch_collected=result.batch_collected,
        budget_reached=result.budget_reached,
    )
    return result
