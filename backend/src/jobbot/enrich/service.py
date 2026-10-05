"""Lecture lente des pages d'offres jobup (docs/05-candidature-externe.md §2) et repérage
des offres expirées (docs/10-ergonomie.md §1).

- d'abord les offres à examiner qui ont un lien jobup, jamais lues ou en échec ;
- puis la revérification, tous les 3 jours, des offres jobup encore utiles ;
- une requête toutes les 10 secondes, 30 au plus par exécution ;
- uniquement des URL de la forme https://www.jobup.ch/<langue>/emplois/detail/<uuid>/ ;
- au plus 3 essais par offre, espacés d'un jour ;
- les autres sites (Indeed) ne se vérifient pas : une offre qu'aucune alerte n'a montrée
  depuis 30 jours est dite expirée (« age »). Une candidature envoyée n'est jamais touchée.
"""

import asyncio
import re
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import and_, func, or_, select, update

from jobbot.core.address import weaker_sources
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
RECHECK_AFTER = timedelta(days=3)
STALE_AFTER = timedelta(days=30)
# Statuts dont l'expiration intéresse Kevin ; « applied » n'est jamais modifié.
WATCHED = (OfferStatus.NEW, OfferStatus.TO_REVIEW, OfferStatus.LATER, OfferStatus.PREPARING)
# Une page d'offre jobup ; une redirection ailleurs (liste, accueil) signifie l'offre retirée.
DETAIL_PAGE = re.compile(r"^https://www\.jobup\.ch/[a-z]{2}/emplois/detail/[0-9a-f-]{36}/")
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
    rechecked: int = 0
    # Offres sans page vérifiable, expirées faute d'alerte depuis 30 jours.
    stale: int = 0


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


async def _recheck_candidates(runtime: Runtime, now: datetime, room: int) -> list[tuple[int, str]]:
    """Offres jobup déjà lues, encore utiles, pas vérifiées depuis 3 jours."""
    if room <= 0:
        return []
    last_check = func.coalesce(Offer.checked_at, Offer.enriched_at)
    async with runtime.sessionmaker() as session:
        rows = await session.execute(
            select(Offer.id, OfferLink.url)
            .join(OfferLink, and_(OfferLink.offer_id == Offer.id, OfferLink.source == Source.JOBUP))
            .where(
                Offer.status.in_(WATCHED),
                Offer.expired_at.is_(None),
                Offer.expiry_override.is_(None),
                Offer.enrich_status == EnrichStatus.OK,
                last_check < now - RECHECK_AFTER,
            )
            .order_by(last_check, Offer.id)
            .limit(room)
        )
        return [(offer_id, url) for offer_id, url in rows]


async def expire_stale(runtime: Runtime, now: datetime) -> int:
    """Sans page à vérifier, une offre absente des alertes depuis 30 jours est expirée."""
    async with runtime.sessionmaker.begin() as session:
        jobup_offers = select(OfferLink.offer_id).where(OfferLink.source == Source.JOBUP)
        result = await session.execute(
            update(Offer)
            .where(
                Offer.expired_at.is_(None),
                Offer.expiry_override.is_(None),
                Offer.status != OfferStatus.APPLIED,
                Offer.last_seen_at < now - STALE_AFTER,
                Offer.id.not_in(jobup_offers),
            )
            .values(expired_at=now, expiry_source="age")
        )
        return int(getattr(result, "rowcount", 0) or 0)


def _gone(page: FetchResult) -> bool:
    """Page introuvable, ou redirection vers autre chose qu'une page d'offre."""
    if page.status_code in (404, 410):
        return True
    return page.status_code == 200 and not DETAIL_PAGE.match(page.final_url)


async def _set_address(runtime: Runtime, offer_id: int, address: str | None) -> None:
    """Adresse du lieu de travail lue sur la page : remplace celle d'une source moins sûre."""
    if not address:
        return
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Offer)
            .where(
                Offer.id == offer_id,
                or_(
                    Offer.company_address_source.is_(None),
                    Offer.company_address_source.in_(weaker_sources("page")),
                ),
            )
            .values(
                company_address=address, company_address_source="page", company_address_url=None
            )
        )


async def _set_logo(runtime: Runtime, offer_id: int, logo: str | None, website: str | None) -> None:
    """Logo et site de l'entreprise lus sur la page, s'ils ne sont pas déjà connus."""
    values = {k: v for k, v in (("logo_url", logo), ("company_website", website)) if v}
    if not values:
        return
    async with runtime.sessionmaker.begin() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            return
        offer.logo_url = offer.logo_url or values.get("logo_url")
        offer.company_website = offer.company_website or values.get("company_website")


async def _expire(runtime: Runtime, offer_id: int, now: datetime) -> None:
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Offer)
            .where(
                Offer.id == offer_id,
                Offer.status != OfferStatus.APPLIED,
                # « Pas expirée » selon Kevin : la page ne le contredit pas.
                Offer.expiry_override.is_(None),
            )
            .values(expired_at=now, expiry_source="page", checked_at=now)
        )


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

        if _gone(page):
            result.expired += 1
            await _record(runtime, offer_id, now, enrich_status=EnrichStatus.EXPIRED)
            await _expire(runtime, offer_id, now)
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
        await _set_address(runtime, offer_id, parsed.address)
        await _set_logo(runtime, offer_id, parsed.logo, parsed.website)
    for offer_id, url in await _recheck_candidates(runtime, now, MAX_PER_RUN - len(candidates)):
        if not ALLOWED_URL.match(url):
            continue
        if result.fetched:
            await sleep(DELAY_SECONDS)
        result.fetched += 1
        result.rechecked += 1
        try:
            checked: FetchResult | None = await fetch(url)
        except httpx.HTTPError as exc:
            log.warning("recheck_fetch_failed", offer_id=offer_id, error=type(exc).__name__)
            checked = None
        if checked is not None and _gone(checked):
            result.expired += 1
            await _expire(runtime, offer_id, now)
            continue
        if checked is not None and checked.status_code == 200:
            # Toujours en ligne : l'adresse, absente des lectures d'avant 0.7.1, est relevée.
            with suppress(PageNotParsable, ValueError):
                found = parse_jobup_page(checked.text, url)
                await _set_address(runtime, offer_id, found.address)
                await _set_logo(runtime, offer_id, found.logo, found.website)
        # Toujours en ligne, ou réponse inattendue : on revérifiera dans 3 jours.
        async with runtime.sessionmaker.begin() as session:
            await session.execute(update(Offer).where(Offer.id == offer_id).values(checked_at=now))
    result.stale = await expire_stale(runtime, now)
    log.info(
        "enrich_finished",
        fetched=result.fetched,
        ok=result.ok,
        expired=result.expired,
        failed=result.failed,
        rechecked=result.rechecked,
        stale=result.stale,
    )
    return result
