"""Adresse des entreprises par le registre IDE, puis sur Internet par l'IA (docs/12 §2.2, 0.7.2).

- une recherche par entreprise (nom normalisé), mise en cache 30 jours ;
- une requête toutes les 5 secondes, 30 au plus par passage ;
- adresse retenue seulement si une seule entreprise active porte ce nom (départagée au besoin
  par le canton ou la ville de l'offre) ; sinon 3 propositions, à choisir dans le détail ;
- faute de correspondance sûre, l'IA cherche sur Internet (nom et ville seulement), au plus
  15 entreprises par passage, dans le plafond mensuel ; une seule fois par entreprise.
"""

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import anthropic
import httpx
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.address import weaker_sources
from jobbot.core.normalize import normalize_location, normalize_text
from jobbot.db.models import Company, Offer, OfferStatus
from jobbot.llm.client import Refused
from jobbot.log import get_logger
from jobbot.registry import uid, web
from jobbot.registry.uid import RegistryCompany
from jobbot.registry.web import WebAddress
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, budget_state, record_call

log = get_logger(__name__)

DELAY_SECONDS = 5.0
MAX_PER_RUN = 30
CACHE_FOR = timedelta(days=30)
WATCHED = (OfferStatus.NEW, OfferStatus.TO_REVIEW, OfferStatus.LATER, OfferStatus.PREPARING)
# Formes juridiques et mots de liaison ignorés pour comparer les noms.
_LEGAL = re.compile(
    r"\b(sa|ag|sarl|gmbh|ltd|inc|llc|sas|snc|cie|co|kg|plc|se|und|et|and|the|la|le|les)\b"
)

sleep: Callable[[float], Awaitable[None]] = asyncio.sleep


def name_key(company: str) -> str:
    return " ".join(_LEGAL.sub(" ", normalize_text(company)).split())


@dataclass(frozen=True)
class Place:
    canton: str | None
    town: str


def choose(company: str, candidates: list[RegistryCompany], place: Place) -> RegistryCompany | None:
    """L'entreprise active au même nom ; départagée par le canton puis la ville de l'offre."""
    key = name_key(company)
    same = [c for c in candidates if c.active and c.street and name_key(c.name) == key]
    if len(same) > 1 and place.canton:
        same = [c for c in same if c.canton == place.canton] or same
    if len(same) > 1 and place.town:
        same = [c for c in same if normalize_text(c.town) == place.town] or same
    return same[0] if len(same) == 1 else None


def _proposals(company: str, candidates: list[RegistryCompany]) -> list[RegistryCompany]:
    """Les 3 propositions actives les plus proches du nom cherché (ordre du registre)."""
    key = name_key(company)
    active = [c for c in candidates if c.active and c.street]
    return sorted(active, key=lambda c: name_key(c.name) != key)[:3]


async def remember(
    session: AsyncSession,
    key: str,
    candidates: list[RegistryCompany],
    chosen: RegistryCompany | None,
    company: str,
) -> None:
    values = {
        "uid": chosen.uid if chosen else None,
        "address": chosen.address if chosen else None,
        "candidates": [c.as_dict() for c in _proposals(company, candidates)],
        "chosen_by": "auto" if chosen else None,
        "looked_up_at": datetime.now(UTC),
    }
    await session.execute(
        insert(Company)
        .values(name_key=key, **values)
        .on_conflict_do_update(index_elements=["name_key"], set_=values)
    )


async def apply_address(
    session: AsyncSession,
    key: str,
    address: str,
    source: str = "registry",
    url: str | None = None,
) -> int:
    """Donne l'adresse trouvée aux offres de cette entreprise qui n'en ont pas de plus sûre."""
    offers = await session.scalars(
        select(Offer).where(
            Offer.company.is_not(None),
            or_(
                Offer.company_address_source.is_(None),
                Offer.company_address_source.in_(weaker_sources(source)),
            ),
        )
    )
    count = 0
    for offer in offers:
        if offer.company and name_key(offer.company) == key:
            offer.company_address, offer.company_address_source = address, source
            offer.company_address_url = url
            count += 1
    return count


@dataclass
class RegistryResult:
    searched: int = 0
    found: int = 0
    ambiguous: int = 0
    failed: int = 0
    web_searched: int = 0
    web_found: int = 0


MAX_WEB_PER_RUN = 15
# Estimation prudente d'une recherche (2 recherches web et le texte), pour le plafond.
WEB_ESTIMATE_USD = Decimal("0.04")


class WebUnavailable(Exception):
    """IA non configurée, plafond atteint ou compte API indisponible : on n'insiste pas."""


async def web_lookup(
    runtime: Runtime, key: str, company: str, town: str | None
) -> WebAddress | None:
    """Cherche l'adresse sur Internet, la met en cache et la donne aux offres de l'entreprise."""
    settings = runtime.settings
    if not settings.llm_configured:
        raise WebUnavailable("IA non configurée")
    async with runtime.sessionmaker() as session:
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if spend + WEB_ESTIMATE_USD * rate > budget:
        raise WebUnavailable("plafond mensuel atteint")
    client = scoring_service.make_client(settings)
    try:
        raw = await client.score(web.request_params(company, town))
    except Refused:
        raw = None
    except anthropic.APIStatusError as exc:
        if account_problem(exc):
            raise WebUnavailable(account_problem(exc) or "") from None
        raise
    found = web.parse_answer(raw.text) if raw else None
    async with runtime.sessionmaker.begin() as session:
        if raw is not None:
            await record_call(session, raw, offer_id=None, rate=rate, purpose="address")
        values: dict[str, object] = {"web_looked_up_at": datetime.now(UTC)}
        if found:
            values |= {"address": found.address, "source_url": found.source_url, "chosen_by": "web"}
        await session.execute(
            insert(Company)
            .values(name_key=key, looked_up_at=datetime.now(UTC), candidates=[], **values)
            .on_conflict_do_update(index_elements=["name_key"], set_=values)
        )
        if found:
            await apply_address(session, key, found.address, "web", found.source_url)
    return found


async def lookup_addresses(runtime: Runtime) -> RegistryResult:
    """Cherche l'adresse des entreprises des offres encore utiles qui n'en ont pas."""
    result = RegistryResult()
    now = datetime.now(UTC)
    async with runtime.sessionmaker() as session:
        rows = (
            await session.execute(
                select(Offer.company, Offer.canton, Offer.location)
                .where(
                    Offer.company.is_not(None),
                    Offer.company_address.is_(None),
                    Offer.status.in_(WATCHED),
                    Offer.expired_at.is_(None),
                )
                .order_by(Offer.first_seen_at.desc())
            )
        ).all()
        cached = {
            key
            for key in await session.scalars(
                select(Company.name_key).where(Company.looked_up_at > now - CACHE_FOR)
            )
        }
    # Toutes les entreprises sans adresse ; le registre n'est interrogé que hors cache.
    needed: dict[str, tuple[str, Place]] = {}
    for company, canton, location in rows:
        key = name_key(company) if company else ""
        if company and key and key not in needed:
            needed[key] = (company, Place(canton, normalize_location(location)))
    todo = {k: v for k, v in needed.items() if k not in cached}

    for index, (key, (company, place)) in enumerate(list(todo.items())[:MAX_PER_RUN]):
        if index:
            await sleep(DELAY_SECONDS)
        result.searched += 1
        try:
            candidates = await uid.search(company)
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("registry_search_failed", error=type(exc).__name__)
            result.failed += 1
            continue
        chosen = choose(company, candidates, place)
        async with runtime.sessionmaker.begin() as session:
            await remember(session, key, candidates, chosen, company)
            if chosen:
                await apply_address(session, key, chosen.address)
        if chosen:
            result.found += 1
        else:
            result.ambiguous += 1
    # Faute de correspondance sûre dans le registre : recherche sur Internet.
    async with runtime.sessionmaker() as session:
        tried = {
            key
            for key in await session.scalars(
                select(Company.name_key).where(
                    or_(Company.address.is_not(None), Company.web_looked_up_at.is_not(None))
                )
            )
        }
    web_todo = [(k, v) for k, v in needed.items() if k not in tried][:MAX_WEB_PER_RUN]
    for key, (company, place) in web_todo:
        try:
            found = await web_lookup(runtime, key, company, place.town or None)
        except WebUnavailable as exc:
            log.info("address_web_stopped", reason=str(exc))
            break
        except (anthropic.APIError, httpx.HTTPError) as exc:
            log.warning("address_web_failed", error=type(exc).__name__)
            continue
        result.web_searched += 1
        result.web_found += bool(found)
    log.info(
        "registry_finished",
        searched=result.searched,
        found=result.found,
        ambiguous=result.ambiguous,
        failed=result.failed,
        web_searched=result.web_searched,
        web_found=result.web_found,
    )
    return result
