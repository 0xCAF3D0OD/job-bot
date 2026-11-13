"""Note et résumé des offres par l'IA (docs/06-note-ia.md).

- Nouvelles offres (peu nombreuses) : appels directs, quelques secondes chacun.
- Rattrapage ou renotation (nombreuses) : un lot, à moitié prix, relevé plus tard.
- Plafond mensuel en CHF : plus aucun appel une fois atteint.
- Seules les offres à examiner sont notées, jamais les offres d'alerte écartées ; une offre
  jamais notée est reprise quel que soit son statut, 3 essais au plus (A2 du 13 novembre).
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import anthropic
from sqlalchemy import ColumnElement, and_, case, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts, plans, platform
from jobbot.db.models import (
    Evaluation,
    LlmBatch,
    LlmCall,
    Offer,
    OfferLink,
    OfferStatus,
    ProfileChunk,
    Setting,
    User,
)
from jobbot.llm.client import BatchItem, RawResult, Refused, ScoreClient, client_factory
from jobbot.llm.pricing import cost_usd
from jobbot.llm.scoring import (
    COMPATIBLE_VERSIONS,
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
KEPT_ASIDE = (OfferStatus.LATER, OfferStatus.PREPARING)
# Écartées par les critères ou par la personne : une offre d'alerte n'y est pas notée (le filtre
# évite de payer l'IA) ; ajoutée à la main, elle l'est quand même (A2 du 13 novembre).
SET_ASIDE = (OfferStatus.FILTERED_OUT, OfferStatus.IGNORED)
# La source d'une offre ajoutée à la main (manual_offers.SOURCE, importé ici sans cycle).
MANUAL_SOURCE = "manual"
# Essais manqués d'affilée avant l'état final « Note impossible ».
MAX_ATTEMPTS = 3
FINAL_NO_TEXT = "sans_texte"
FINAL_EMPTY = "reponse_vide"
FINAL_ERROR = "erreur"
FINAL_BACKLOG = "a_rattraper"

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
    # Les offres notées du mois sont épuisées (la formule, docs/125).
    limit_reached: bool = False
    # Offres sans aucun texte, passées en « Note impossible » sans appel.
    no_text: int = 0


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


@dataclass(frozen=True)
class Budget:
    spend: Decimal  # dépense du mois du compte, en CHF
    cap: Decimal  # plafond du compte
    effective: Decimal  # ce que le compte peut atteindre, plafond total de la plateforme compris
    rate: Decimal  # taux USD → CHF
    platform_reached: bool  # le plafond total est atteint


async def budget_details(session: AsyncSession, now: datetime) -> Budget:
    """Plafond du compte (docs/65 §4) : celui des Réglages pour l'exploitant, celui que
    l'exploitant a fixé pour un compte invité ; et, pour tous, le plafond total."""
    spend = await month_spend_chf(session, now)
    if await accounts.is_owner(session):
        cap = await _setting(session, "llm_monthly_budget_chf", Decimal("10"))
    else:
        user = await session.get(User, accounts.current())
        fixed = user.ai_budget_chf if user else None
        cap = fixed if fixed is not None else platform.ACCOUNT_AI_BUDGET_CHF
    start = now.astimezone(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_spend = Decimal(str(await session.scalar(select(func.platform_month_spend(start))) or 0))
    left = await platform.total_ai_budget(session) - total_spend
    rate = await _setting(session, "usd_chf_rate", Decimal("0.8"))
    return Budget(
        spend=spend,
        cap=cap,
        effective=min(cap, spend + max(left, Decimal(0))),
        rate=rate,
        platform_reached=left <= 0,
    )


async def budget_state(session: AsyncSession, now: datetime) -> tuple[Decimal, Decimal, Decimal]:
    """(dépense du mois en CHF, plafond en CHF, taux USD→CHF)."""
    budget = await budget_details(session, now)
    return budget.spend, budget.effective, budget.rate


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
    session: AsyncSession,
    current_hash: str,
    *,
    include_stale_profile: bool,
    has_profile: bool = True,
) -> list[Offer]:
    """Offres à examiner sans note à jour (jamais notées, consignes changées, ou texte
    complet arrivé après une note faite sur l'extrait). Avec `include_stale_profile`,
    aussi celles notées avec un autre profil (renotation sur clic de Kevin).

    Une offre jamais notée est reprise quel que soit son statut (A2 du 13 novembre) : passer en
    préparation, la garder ou l'envoyer avant sa note ne l'annule plus. Seules les offres d'alerte
    écartées (par les critères ou par la personne) restent sans note ; ajoutée à la main, l'offre
    est notée quand même. Une note faite sans profil (note vide) est refaite dès que le profil
    existe. Un état final (`score_final`) n'est plus repris."""
    manual = (
        select(OfferLink.id)
        .where(OfferLink.offer_id == Offer.id, OfferLink.source == MANUAL_SOURCE)
        .exists()
    )
    eligible = and_(
        Evaluation.score_final.is_(None),
        or_(Offer.status.not_in(SET_ASIDE), manual),
    )
    never: list[ColumnElement[bool]] = [Evaluation.id.is_(None), Evaluation.scored_at.is_(None)]
    if has_profile:
        # Notée sans profil : résumé fait, note vide ; à refaire avec le profil (offre 796).
        never.append(
            and_(
                Evaluation.score.is_(None),
                Evaluation.scored_at.is_not(None),
                or_(Evaluation.profile_hash.is_(None), Evaluation.profile_hash != current_hash),
            )
        )
    needs = [
        Evaluation.prompt_version.not_in(COMPATIBLE_VERSIONS),
        and_(Offer.description.is_not(None), Evaluation.summary_partial.is_(True)),
    ]
    # Consignes changées (score-v2 : mots-clés) : les offres mises de côté ou en préparation
    # sont aussi renotées, pour avoir leurs étiquettes (docs/11 §3).
    kept_aside = and_(
        Offer.status.in_(KEPT_ASIDE),
        Evaluation.scored_at.is_not(None),
        Evaluation.prompt_version.not_in(COMPATIBLE_VERSIONS),
    )
    if include_stale_profile:
        needs.append(Evaluation.profile_hash != current_hash)
        needs.append(Evaluation.score_error.is_not(None))
    rows = await session.scalars(
        select(Offer)
        .outerjoin(Evaluation, Evaluation.offer_id == Offer.id)
        .where(
            Offer.expired_at.is_(None),
            # Un doublon n'est pas noté : son offre gardée l'est (docs/30 §3).
            Offer.duplicate_of.is_(None),
            # Candidature spontanée : pas d'annonce à comparer au profil (docs/39 §4).
            Offer.spontaneous.is_(False),
            or_(
                and_(eligible, or_(*never)),
                and_(Offer.status.in_(TO_SCORE), or_(*needs)),
                kept_aside,
            ),
        )
        .order_by(Offer.first_seen_at.desc(), Offer.id.desc())
    )
    pending = await _pending_batch_offers(session)
    return [offer for offer in rows if offer.id not in pending]


async def score_soon(runtime: Runtime) -> None:
    """La notation de ce compte, mise en file tout de suite au lieu d'attendre le passage des
    10 minutes (A2 du 13 novembre) : offre ajoutée, ou offre écartée que la personne récupère.
    Si la mise en file échoue, le passage des 10 minutes la reprend."""
    if not runtime.settings.llm_configured:
        return
    # Import ici : worker.tasks importe ce module.
    from jobbot.worker.queue import enqueue
    from jobbot.worker.tasks.score import SCORE_JOB

    try:
        await enqueue(runtime.settings, SCORE_JOB)
    except Exception as exc:
        log.warning("score_not_queued", error=type(exc).__name__)


async def score_if_unscored(runtime: Runtime, offer_id: int) -> None:
    """Notation tout de suite si l'offre attend encore sa note (pas notée, pas d'état final)."""
    async with runtime.sessionmaker() as session:
        row = (
            await session.execute(
                select(Evaluation.score, Evaluation.scored_at, Evaluation.score_final).where(
                    Evaluation.offer_id == offer_id
                )
            )
        ).first()
    if row is None or (row.score is None and row.scored_at is None and row.score_final is None):
        await score_soon(runtime)


def has_text(offer: Offer) -> bool:
    """Rien à lire (ni texte, ni extrait de l'alerte) : la note est impossible, sans appel."""
    return bool((offer.description or "").strip() or (offer.snippet or "").strip())


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
    prompt_version: str = PROMPT_VERSION,
    failure: str | None = None,
) -> None:
    """Range la note, ou l'échec. `failure` (FINAL_EMPTY ou FINAL_ERROR) compte un essai manqué :
    au MAX_ATTEMPTS-ième d'affilée, l'offre passe dans l'état final « Note impossible » avec cette
    raison, et n'est plus reprise. Une note réussie remet le compte à zéro."""
    now = datetime.now(UTC)
    values: dict[str, Any] = {
        "model": model,
        "prompt_version": prompt_version,
        "profile_hash": hash_,
        "score_error": error,
    }
    inserted: dict[str, Any] = {}
    if output is None and failure is not None:
        attempts = func.coalesce(Evaluation.score_attempts, 0) + 1
        values |= {
            "score_attempts": attempts,
            "score_final": case((attempts >= MAX_ATTEMPTS, failure), else_=None),
        }
        inserted = {"score_attempts": 1, "score_final": failure if MAX_ATTEMPTS <= 1 else None}
    if output is not None:
        values |= {"score_attempts": 0, "score_final": None}
        values |= {
            "score": output.score,
            "summary_role": output.summary_role,
            "summary_asks": output.summary_asks,
            "summary_offers": output.summary_offers,
            "summary_partial": partial,
            "strengths": [p.model_dump() for p in output.strengths],
            "gaps": [p.model_dump() for p in output.gaps],
            "keywords_role": output.keywords_role,
            "keywords_asks": [k.model_dump() for k in output.keywords_asks],
            "keywords_offers": output.keywords_offers,
            "remote": output.remote,
            "remote_days": output.remote_days,
            "remote_region": output.remote_region,
            "remote_from_switzerland": output.remote_from_switzerland,
            "scam_signals": [signal.model_dump() for signal in output.scam_signals],
            "why": output.why,
            "level": output.level,
            "level_detail": output.level_detail,
            "score_parts": [p.model_dump() for p in output.parts],
            "score_tip": output.tip.model_dump() if output.tip else None,
            "scored_at": now,
        }
    # Une offre pas encore passée par le filtre n'a pas de ligne : on la crée, le filtre
    # complétera ses colonnes.
    await session.execute(
        insert(Evaluation)
        .values(
            offer_id=offer_id,
            filter_passed=True,
            filter_reasons=[],
            criteria_hash="",
            **(values | inserted),
        )
        .on_conflict_do_update(index_elements=["user_id", "offer_id"], set_=values)
    )


def _failure(text: str) -> str:
    """Réponse vide de l'IA, ou réponse illisible (erreur)."""
    return FINAL_EMPTY if not text.strip() else FINAL_ERROR


async def _store_no_text(session: AsyncSession, offer_id: int, hash_: str) -> None:
    """Rien à lire : état final direct, sans appel à l'IA (cas de l'offre 619)."""
    values: dict[str, Any] = {"score_final": FINAL_NO_TEXT, "profile_hash": hash_}
    await session.execute(
        insert(Evaluation)
        .values(
            offer_id=offer_id, filter_passed=True, filter_reasons=[], criteria_hash="", **values
        )
        .on_conflict_do_update(index_elements=["user_id", "offer_id"], set_=values)
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
                if item.result is None and item.error in ("canceled", "expired"):
                    # Lot annulé ou expiré : pas la faute de l'offre, elle sera renotée.
                    continue
                if item.result is None:
                    await _store(
                        session,
                        offer.id,
                        output=None,
                        model=runtime.settings.score_model,
                        hash_=hash_,
                        partial=partial,
                        error=f"lot : {item.error}",
                        prompt_version=batch.prompt_version,
                        failure=FINAL_ERROR,
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
                        prompt_version=batch.prompt_version,
                        failure=_failure(item.result.text),
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
                    prompt_version=batch.prompt_version,
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
            request_params(settings.score_model, settings.llm_effort, profile, offer_data(offer)),
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
        session.add(
            LlmBatch(
                provider_batch_id=batch_id,
                offer_ids=[o.id for o in offers],
                prompt_version=PROMPT_VERSION,
            )
        )
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
        params = request_params(settings.score_model, settings.llm_effort, profile, data)
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
                    model=settings.score_model,
                    hash_=hash_,
                    partial=data.partial,
                    error=error,
                    failure=FINAL_ERROR,
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
                    failure=_failure(raw.text),
                )
                result.failed += 1
                continue
            await _store(
                session, offer.id, output=output, model=raw.model, hash_=hash_, partial=data.partial
            )
            result.scored += 1


async def score_offer(runtime: Runtime, offer_id: int) -> int | None:
    """Note une seule offre, tout de suite, avec le profil actuel (correction d'une note,
    docs/114). Au plafond ou sans IA, la note reste ; elle sera refaite sur « Renoter »."""
    async with runtime.sessionmaker() as session:
        profile = await active_profile(session)
        offer = await session.get(Offer, offer_id)
        allowed, _ = await within_plan(session, [offer] if offer else [])
    if offer is None:
        return None
    # Demande explicite (texte arrivé, correction, ajout) : les essais repartent de zéro.
    async with runtime.sessionmaker.begin() as session:
        if not has_text(offer):
            await _store_no_text(session, offer_id, profile_hash(profile))
            return None
        await session.execute(
            update(Evaluation)
            .where(Evaluation.offer_id == offer_id)
            .values(score_attempts=0, score_final=None)
        )
    if not allowed:
        log.info("score_offer_limit_reached", offer_id=offer_id)
        async with runtime.sessionmaker() as session:
            return await session.scalar(
                select(Evaluation.score).where(Evaluation.offer_id == offer_id)
            )
    result = ScoringResult()
    try:
        await _score_direct(runtime, make_client(runtime.settings), [offer], profile, result)
    except ScoringUnavailable as exc:
        log.warning("score_offer_unavailable", problem=str(exc))
    async with runtime.sessionmaker() as session:
        return await session.scalar(select(Evaluation.score).where(Evaluation.offer_id == offer_id))


async def within_plan(session: AsyncSession, todo: list[Offer]) -> tuple[list[Offer], bool]:
    """Les offres que la formule permet de noter ce mois-ci (docs/125) : une offre déjà notée ce
    mois se renote sans compter ; les nouvelles, dans la limite qui reste. Vrai si on en laisse."""
    remaining = await plans.left(session, plans.SCORE)
    if remaining is None:
        return todo, False
    counted = await plans.scored_this_month(session)
    fresh = [o.id for o in todo if o.id not in counted]
    allowed = counted | set(fresh[:remaining])
    return [o for o in todo if o.id in allowed], len(fresh) > remaining


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
        hash_ = profile_hash(profile)
        todo = await candidates(
            session, hash_, include_stale_profile=rescore_profile, has_profile=bool(profile)
        )
    # Rien à lire : « Note impossible » tout de suite, sans appel ni décompte de la formule.
    blank = [o for o in todo if not has_text(o)]
    if blank:
        async with runtime.sessionmaker.begin() as session:
            for offer in blank:
                await _store_no_text(session, offer.id, hash_)
        result.no_text = len(blank)
        todo = [o for o in todo if has_text(o)]
    async with runtime.sessionmaker() as session:
        todo, result.limit_reached = await within_plan(session, todo)
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
        no_text=result.no_text,
        batch_submitted=result.batch_submitted,
        batch_collected=result.batch_collected,
        budget_reached=result.budget_reached,
        limit_reached=result.limit_reached,
    )
    return result
