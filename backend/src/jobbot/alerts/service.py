"""Mes alertes (docs/20 §1) : recherches proposées, adresses de recherche par site, état.

La plateforme ne crée pas d'alerte sur les sites (comptes, protections contre les robots) :
elle ouvre la recherche déjà remplie et vérifie ensuite, dans le journal, que l'alerte arrive.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_text
from jobbot.db.models import AlertSearch, AlertSetup, Search, Setting, Site
from jobbot.filtering.service import load_criteria
from jobbot.news import domain

PROPOSED_KEY = "alert_searches_proposed"
MAX_PROPOSED = 8
# « Créée » depuis 3 jours sans alerte reçue : rappel sur Aujourd'hui.
WAIT_BEFORE_REMINDER = timedelta(days=3)

# Page de résultats déjà remplie, d'où l'on crée l'alerte (adresses vérifiées le 2026-10-07,
# sauf Indeed, qui refuse les lectures automatiques).
SEARCH_URLS: dict[str, tuple[str, str, str]] = {
    "jobup": ("https://www.jobup.ch/fr/emplois/?", "term", "location"),
    "jobsch": ("https://www.jobs.ch/fr/offres-emplois/?", "term", "location"),
    "linkedin": ("https://www.linkedin.com/jobs/search/?", "keywords", "location"),
    "indeed": ("https://ch-fr.indeed.com/jobs?", "q", "l"),
}


def search_url(site: Site, terms: str, location: str | None) -> str | None:
    """Recherche déjà remplie sur le site ; sinon la page du site (sites ajoutés)."""
    known = SEARCH_URLS.get(site.slug)
    if known is None:
        return site.url if site.url and site.url.startswith("https://") else None
    base, term_key, location_key = known
    query = {term_key: terms}
    if location:
        query[location_key] = location
    return base + urlencode(query)


def is_canton(value: str) -> bool:
    """« VD », « GE » : un code de canton n'est pas un lieu de recherche utile sur les sites."""
    return len(value) == 2 and value.isalpha() and value.isupper()


async def propose(session: AsyncSession) -> None:
    """Une seule fois : chaque mot-clé de « Mon domaine » avec chaque lieu de « Ce que je
    cherche » (au plus 8)."""
    if await session.scalar(select(Setting.value).where(Setting.key == PROPOSED_KEY)):
        return
    keywords = (await domain.keywords(session))[:4]
    criteria = await load_criteria(session)
    places = [loc for loc in criteria.locations if not is_canton(loc)][:4]
    locations: list[str | None] = list(places) if places else [None]
    added = 0
    for keyword in keywords:
        for location in locations:
            if added >= MAX_PROPOSED:
                break
            session.add(AlertSearch(terms=keyword, location=location))
            added += 1
    session.add(Setting(key=PROPOSED_KEY, value=True))


@dataclass(frozen=True)
class Cell:
    site: str
    url: str | None
    status: str  # received | created | todo
    received_at: datetime | None
    created_at: datetime | None


def _received(searches: list[Search], site: str, terms: str) -> datetime | None:
    """Dernière alerte de ce site dont l'objet ou le libellé contient tous les mots."""
    words = normalize_text(terms).split()
    if not words:
        return None
    latest: datetime | None = None
    for row in searches:
        if row.source != site:
            continue
        text = f" {normalize_text(f'{row.alert_label or ""} {row.subject or ""}')} "
        if all(f" {word} " in text for word in words):
            latest = max(latest, row.received_at) if latest else row.received_at
    return latest


async def cells(session: AsyncSession, search: AlertSearch, sites: list[Site]) -> list[Cell]:
    since = datetime.now(UTC) - timedelta(days=60)
    journal = list(
        await session.scalars(
            select(Search).where(
                Search.received_at >= since, Search.source.in_([s.slug for s in sites])
            )
        )
    )
    setups = {
        s.site: s.created_at
        for s in await session.scalars(select(AlertSetup).where(AlertSetup.search_id == search.id))
    }
    found: list[Cell] = []
    for site in sites:
        received = _received(journal, site.slug, search.terms)
        created = setups.get(site.slug)
        status = "received" if received else "created" if created else "todo"
        found.append(
            Cell(
                site.slug,
                search_url(site, search.terms, search.location),
                status,
                received,
                created,
            )
        )
    return found


async def waiting(session: AsyncSession) -> int:
    """Alertes créées depuis 3 jours ou plus qui n'ont encore rien envoyé (rappel)."""
    sites = list(await session.scalars(select(Site).where(Site.active.is_(True))))
    limit = datetime.now(UTC) - WAIT_BEFORE_REMINDER
    count = 0
    for search in await session.scalars(select(AlertSearch).where(AlertSearch.active.is_(True))):
        for cell in await cells(session, search, sites):
            if cell.status == "created" and cell.created_at and cell.created_at <= limit:
                count += 1
    return count
