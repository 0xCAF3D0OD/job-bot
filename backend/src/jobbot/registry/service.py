"""Adresse des entreprises par le registre IDE, pour les offres sans page lisible (docs/12 §2.2).

- une recherche par entreprise (nom normalisé), mise en cache 30 jours ;
- une requête toutes les 5 secondes, 30 au plus par passage ;
- adresse retenue seulement si une seule entreprise active porte ce nom (départagée au besoin
  par le canton ou la ville de l'offre) ; sinon 3 propositions, à choisir dans le détail.
"""

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.address import weaker_sources
from jobbot.core.normalize import normalize_location, normalize_text
from jobbot.db.models import Company, Offer, OfferStatus
from jobbot.log import get_logger
from jobbot.registry import uid
from jobbot.registry.uid import RegistryCompany
from jobbot.runtime import Runtime

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


async def apply_address(session: AsyncSession, key: str, address: str) -> int:
    """Donne l'adresse trouvée aux offres de cette entreprise qui n'en ont pas de plus sûre."""
    offers = await session.scalars(
        select(Offer).where(
            Offer.company.is_not(None),
            or_(
                Offer.company_address_source.is_(None),
                Offer.company_address_source.in_(weaker_sources("registry")),
            ),
        )
    )
    count = 0
    for offer in offers:
        if offer.company and name_key(offer.company) == key:
            offer.company_address, offer.company_address_source = address, "registry"
            count += 1
    return count


@dataclass
class RegistryResult:
    searched: int = 0
    found: int = 0
    ambiguous: int = 0
    failed: int = 0


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
    todo: dict[str, tuple[str, Place]] = {}
    for company, canton, location in rows:
        if not company:
            continue
        key = name_key(company)
        if key and key not in cached and key not in todo:
            todo[key] = (company, Place(canton, normalize_location(location)))

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
    log.info(
        "registry_finished",
        searched=result.searched,
        found=result.found,
        ambiguous=result.ambiguous,
        failed=result.failed,
    )
    return result
