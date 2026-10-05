"""Lecture lente des pages d'offres jobup (docs/05-candidature-externe.md §2).

- seulement les offres à examiner qui ont un lien jobup, jamais lues ou en échec ;
- une requête toutes les 10 secondes, 30 au plus par exécution ;
- uniquement des URL de la forme https://www.jobup.ch/<langue>/emplois/detail/<uuid>/ ;
- au plus 3 essais par offre, espacés d'un jour.
"""

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import and_, or_, select, update

from jobbot.db.models import EnrichStatus, Offer, OfferLink, OfferStatus, Source
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.sources.jobup_page import PageNotParsable, parse_jobup_page

log = get_logger(__name__)

USER_AGENT = "job-bot/0.3 (usage personnel)"
DELAY_SECONDS = 10.0
MAX_PER_RUN = 30
MAX_ATTEMPTS = 3
RETRY_AFTER = timedelta(days=1)
ALLOWED_URL = re.compile(
    r"^https://www\.jobup\.ch/[a-z]{2}/emplois/detail/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}/$"
)


@dataclass(frozen=True)
class FetchResult:
    status_code: int
    text: str
    final_url: str


Fetcher = Callable[[str], Awaitable[FetchResult]]


async def http_fetch(url: str) -> FetchResult:
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT, "Accept-Language": "fr-CH,fr;q=0.9"},
        timeout=20,
        follow_redirects=True,
    ) as client:
        response = await client.get(url)
        return FetchResult(response.status_code, response.text, str(response.url))


# Remplaçables dans les tests (pas de réseau, pas d'attente réelle).
fetch: Fetcher = http_fetch
sleep: Callable[[float], Awaitable[None]] = asyncio.sleep


@dataclass
class EnrichResult:
    fetched: int = 0
    ok: int = 0
    expired: int = 0
    failed: int = 0


async def _candidates(runtime: Runtime, now: datetime) -> list[tuple[int, str]]:
    retry_before = now - RETRY_AFTER
    async with runtime.sessionmaker.begin() as session:
        # Les offres sans lien jobup n'ont pas de page lisible.
        jobup_offers = select(OfferLink.offer_id).where(OfferLink.source == Source.JOBUP)
        await session.execute(
            update(Offer)
            .where(Offer.enrich_status == EnrichStatus.PENDING, Offer.id.not_in(jobup_offers))
            .values(enrich_status=EnrichStatus.SKIPPED)
        )
        rows = await session.execute(
            select(Offer.id, OfferLink.url)
            .join(OfferLink, and_(OfferLink.offer_id == Offer.id, OfferLink.source == Source.JOBUP))
            .where(
                Offer.status.in_((OfferStatus.NEW, OfferStatus.TO_REVIEW)),
                or_(
                    Offer.enrich_status == EnrichStatus.PENDING,
                    and_(
                        Offer.enrich_status == EnrichStatus.FAILED,
                        Offer.enrich_attempts < MAX_ATTEMPTS,
                        Offer.enriched_at < retry_before,
                    ),
                ),
            )
            .order_by(Offer.first_seen_at.desc(), Offer.id.desc())
            .limit(MAX_PER_RUN)
        )
        return [(offer_id, url) for offer_id, url in rows]


async def _record(runtime: Runtime, offer_id: int, now: datetime, **values: object) -> None:
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Offer)
            .where(Offer.id == offer_id)
            .values(enriched_at=now, enrich_attempts=Offer.enrich_attempts + 1, **values)
        )


async def enrich(runtime: Runtime) -> EnrichResult:
    result = EnrichResult()
    now = datetime.now(UTC)
    candidates = await _candidates(runtime, now)
    for index, (offer_id, url) in enumerate(candidates):
        if not ALLOWED_URL.match(url):
            log.warning("enrich_url_refused", offer_id=offer_id)
            await _record(runtime, offer_id, now, enrich_status=EnrichStatus.SKIPPED)
            continue
        if index:
            await sleep(DELAY_SECONDS)
        result.fetched += 1
        try:
            page = await fetch(url)
        except httpx.HTTPError as exc:
            log.warning("enrich_fetch_failed", offer_id=offer_id, error=type(exc).__name__)
            result.failed += 1
            await _record(runtime, offer_id, now, enrich_status=EnrichStatus.FAILED)
            continue

        if page.status_code in (404, 410):
            result.expired += 1
            await _record(runtime, offer_id, now, enrich_status=EnrichStatus.EXPIRED)
            continue
        if page.status_code != 200 or not page.final_url.startswith("https://www.jobup.ch/"):
            log.warning("enrich_unexpected_response", offer_id=offer_id, status=page.status_code)
            result.failed += 1
            await _record(runtime, offer_id, now, enrich_status=EnrichStatus.FAILED)
            continue
        try:
            parsed = parse_jobup_page(page.text, url)
        except (PageNotParsable, ValueError) as exc:
            log.warning("enrich_parse_failed", offer_id=offer_id, error=type(exc).__name__)
            result.failed += 1
            await _record(runtime, offer_id, now, enrich_status=EnrichStatus.FAILED)
            continue

        result.ok += 1
        await _record(
            runtime,
            offer_id,
            now,
            enrich_status=EnrichStatus.OK,
            apply_url=parsed.apply_url,
            apply_kind=parsed.apply_kind,
            description=parsed.description,
            employment_type=parsed.employment_type,
        )
    log.info(
        "enrich_finished",
        fetched=result.fetched,
        ok=result.ok,
        expired=result.expired,
        failed=result.failed,
    )
    return result
