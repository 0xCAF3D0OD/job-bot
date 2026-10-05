"""Lecture et enregistrement des prérequis, et application du filtre aux offres."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.filter import ContractType, Criteria, Language, OfferFacts, canton_of, evaluate
from jobbot.core.normalize import normalize_location
from jobbot.db.models import Criterion, Evaluation, Offer, OfferStatus
from jobbot.log import get_logger
from jobbot.runtime import Runtime

log = get_logger(__name__)

# Statuts que le filtre peut changer. Les autres (plus tard, ignorée, en préparation,
# envoyée) ont été posés par Kevin : le filtre n'y touche jamais.
FILTERABLE = (OfferStatus.NEW, OfferStatus.TO_REVIEW, OfferStatus.FILTERED_OUT)


async def load_criteria(session: AsyncSession) -> Criteria:
    rows = {c.kind: c.value for c in await session.scalars(select(Criterion))}
    return Criteria(
        locations=tuple(rows.get("locations", [])),
        remote_ok=bool(rows.get("remote_ok", False)),
        min_rate=rows.get("min_rate"),
        excluded_types=tuple(ContractType(v) for v in rows.get("excluded_types", [])),
        banned_words=tuple(rows.get("banned_words", [])),
        unspoken_languages=tuple(Language(v) for v in rows.get("unspoken_languages", [])),
    )


async def save_criteria(session: AsyncSession, criteria: Criteria) -> None:
    values: dict[str, Any] = {
        "locations": list(criteria.locations),
        "remote_ok": criteria.remote_ok,
        "min_rate": criteria.min_rate,
        "excluded_types": [t.value for t in criteria.excluded_types],
        "banned_words": list(criteria.banned_words),
        "unspoken_languages": [lang.value for lang in criteria.unspoken_languages],
    }
    for kind, value in values.items():
        await session.execute(
            insert(Criterion)
            .values(kind=kind, value=value)
            .on_conflict_do_update(index_elements=["kind"], set_={"value": value})
        )


def _city_cantons(offers: list[Offer]) -> dict[str, str]:
    """Canton de chaque ville, appris des offres qui l'indiquent (« Prilly, VD »), pour les
    offres qui ne donnent que la ville (jobup)."""
    known: dict[str, str] = {}
    for offer in offers:
        canton = canton_of(offer.location)
        if canton:
            known.setdefault(normalize_location(offer.location), canton)
    return known


@dataclass
class FilterResult:
    examined: int = 0
    to_review: int = 0
    filtered_out: int = 0


async def run_filter(runtime: Runtime) -> FilterResult:
    result = FilterResult()
    async with runtime.sessionmaker.begin() as session:
        criteria = await load_criteria(session)
        digest = criteria.digest()
        all_offers = list(await session.scalars(select(Offer)))
        city_cantons = _city_cantons(all_offers)
        for offer in all_offers:
            if offer.status not in FILTERABLE:
                continue
            evaluation = evaluate(
                OfferFacts(
                    title=offer.title,
                    company=offer.company,
                    location=offer.location,
                    # Texte complet de l'annonce (jobup) quand il est connu.
                    snippet=" ".join(
                        part
                        for part in (offer.snippet, offer.employment_type, offer.description)
                        if part
                    ),
                    rate_min=offer.rate_min,
                    rate_max=offer.rate_max,
                ),
                criteria,
                city_cantons,
            )
            reasons = [{"rule": r.rule, "message": r.message} for r in evaluation.reasons]
            await session.execute(
                insert(Evaluation)
                .values(
                    offer_id=offer.id,
                    filter_passed=evaluation.passed,
                    filter_reasons=reasons,
                    criteria_hash=digest,
                )
                .on_conflict_do_update(
                    index_elements=["offer_id"],
                    set_={
                        "filter_passed": evaluation.passed,
                        "filter_reasons": reasons,
                        "criteria_hash": digest,
                        "evaluated_at": func.now(),
                    },
                )
            )
            offer.status = OfferStatus.TO_REVIEW if evaluation.passed else OfferStatus.FILTERED_OUT
            result.examined += 1
            if evaluation.passed:
                result.to_review += 1
            else:
                result.filtered_out += 1
    log.info(
        "filter_finished",
        examined=result.examined,
        to_review=result.to_review,
        filtered_out=result.filtered_out,
    )
    return result
