"""Les premières offres d'un compte (docs/104, 0.80.0) : la recherche publique de jobup.

Juste après l'accueil, jobA1 lit une fois la page de recherche publique de jobup pour le
métier et les lieux du compte, sans se connecter à rien : les offres arrivent dès le premier
jour, avant les alertes. La page porte la liste des offres en `JobPosting` (schema.org).

Sources écartées (vérifié le 2026-10-21) : Indeed refuse les robots (403) et Job-Room
interdit sa recherche (`Disallow: /job-search/`) ; jobA1 ne contourne ni l'un ni l'autre.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.alerts.service import is_canton
from jobbot.collect.service import ingest_offers
from jobbot.db.models import (
    PUBLIC_SEARCH_PREFIX,
    AlertSearch,
    ParseStatus,
    Search,
    Setting,
    Source,
)
from jobbot.filtering.service import load_criteria
from jobbot.log import get_logger
from jobbot.logos import service as logos
from jobbot.news import domain
from jobbot.runtime import Runtime
from jobbot.sources.base import RawOffer
from jobbot.sources.jobposting import LD_JSON, location, text, types
from jobbot.worker.queue import enqueue

log = get_logger(__name__)

KEY = "first_offers"
SEARCH_URL = "https://www.jobup.ch/fr/emplois/?"
PER_SOURCE = 20
# jobup ne montre aux robots que la première page (10 offres ; `page=2` y renvoie) : jobA1
# ne le contourne pas et fait plutôt jusqu'à quatre recherches (métier et lieux).
MAX_SEARCHES = 4
DELAY_SECONDS = 2.0
MAX_PAGE_BYTES = 3_000_000
_UUID_LEN = 36


@dataclass
class FirstOffersResult:
    searches: int = 0
    found: int = 0
    new_offers: int = 0
    queries: list[str] = field(default_factory=list)


def postings(page: str) -> list[dict[str, Any]]:
    """Les `JobPosting` d'une page de résultats (dans une `ItemList`), dans l'ordre."""
    found: list[dict[str, Any]] = []
    for match in LD_JSON.finditer(page):
        try:
            data = json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            continue
        stack: list[Any] = [data]
        while stack:
            item = stack.pop(0)
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                if "JobPosting" in types(item):
                    found.append(item)
                    continue
                for key in ("@graph", "itemListElement", "item"):
                    if isinstance(item.get(key), (list, dict)):
                        stack.append(item[key])
    return found


def raw_offer(posting: dict[str, Any]) -> RawOffer | None:
    title = text(posting.get("title"))
    url = posting.get("url")
    if not title or not isinstance(url, str) or not url.startswith("https://www.jobup.ch/"):
        return None
    org = posting.get("hiringOrganization")
    company = org.get("name") if isinstance(org, dict) else None
    identifier = posting.get("identifier")
    external_id = identifier.get("value") if isinstance(identifier, dict) else None
    snippet = text(posting.get("description"))
    return RawOffer(
        title=title.splitlines()[0][:300],
        url=url,
        company=" ".join(str(company).split())[:300] if company else None,
        location=location(posting),
        snippet=snippet[:500] if snippet else None,
        external_id=str(external_id)
        if external_id and len(str(external_id)) == _UUID_LEN
        else None,
    )


async def queries(session: AsyncSession) -> list[tuple[str, str | None]]:
    """Ce que cherche le compte : ses recherches d'alerte, sinon son métier et ses lieux."""
    rows = (
        await session.execute(
            select(AlertSearch.terms, AlertSearch.location)
            .where(AlertSearch.active.is_(True))
            .order_by(AlertSearch.id)
        )
    ).all()
    found = [(terms.strip(), (location or "").strip() or None) for terms, location in rows]
    if not found:
        words = await domain.keywords(session)
        criteria = await load_criteria(session)
        places: list[str | None] = []
        places.extend(p for p in criteria.locations if not is_canton(p))
        # Le métier d'abord, dans chaque lieu ; puis le mot suivant de « Mon domaine ».
        found = [(w, p) for w in words[:2] for p in places[:2] or [None]]
    unique = list(dict.fromkeys((t, loc) for t, loc in found if t))
    return unique[:MAX_SEARCHES]


async def fetch(client: httpx.AsyncClient, url: str) -> str:
    data, _final = await logos._get(client, url, MAX_PAGE_BYTES)
    return data.decode("utf-8", errors="replace")


async def search_jobup(
    client: httpx.AsyncClient, terms: str, location: str | None, limit: int
) -> list[RawOffer]:
    """Les offres de la recherche publique (la première page, 10 offres)."""
    query = {"term": terms, **({"location": location} if location else {})}
    html = await fetch(client, SEARCH_URL + urlencode(query))
    offers: dict[str, RawOffer] = {}
    for offer in map(raw_offer, postings(html)):
        if offer is not None:
            offers.setdefault(offer.url, offer)
    return list(offers.values())[:limit]


async def state(session: AsyncSession) -> dict[str, Any]:
    value = await session.scalar(select(Setting.value).where(Setting.key == KEY))
    return value if isinstance(value, dict) else {}


async def _save(session: AsyncSession, value: dict[str, Any]) -> None:
    statement = insert(Setting).values(key=KEY, value=value)
    await session.execute(
        statement.on_conflict_do_update(
            index_elements=["user_id", "key"], set_={"value": statement.excluded.value}
        )
    )


async def mark_queued(session: AsyncSession) -> None:
    await _save(session, {**await state(session), "status": "queued"})


async def run_first_offers(runtime: Runtime) -> FirstOffersResult:
    """La recherche publique pour le compte en cours ; une recherche par (mots, lieu), 20
    offres au plus pour jobup. Les offres entrent comme celles d'une alerte."""
    result = FirstOffersResult()
    async with runtime.sessionmaker() as session:
        wanted = await queries(session)
    if not wanted:
        async with runtime.sessionmaker.begin() as session:
            await _save(session, {"status": "no_trade"})
        return result
    now = datetime.now(UTC)
    collected: dict[str, RawOffer] = {}
    async with httpx.AsyncClient(
        timeout=10, follow_redirects=False, headers={"User-Agent": logos.USER_AGENT}
    ) as client:
        for index, (terms, location) in enumerate(wanted):
            if index:
                await asyncio.sleep(DELAY_SECONDS)
            remaining = PER_SOURCE - len(collected)
            if remaining <= 0:
                break
            try:
                found = await search_jobup(client, terms, location, remaining)
            except (httpx.HTTPError, logos.Refused) as exc:
                log.warning("first_offers_failed", error=type(exc).__name__)
                continue
            result.searches += 1
            result.queries.append(f"{terms} · {location}" if location else terms)
            for offer in found:
                collected.setdefault(offer.url, offer)
    offers = list(collected.values())
    result.found = len(offers)
    key = f"public/{uuid.uuid4()}.json"
    runtime.storage.put(
        key,
        json.dumps(
            {"source": "jobup", "queries": result.queries, "offers": [o.url for o in offers]},
            ensure_ascii=False,
        ).encode(),
    )
    async with runtime.sessionmaker.begin() as session:
        if result.searches:
            search = Search(
                source=Source.JOBUP,
                message_id=f"{PUBLIC_SEARCH_PREFIX}{uuid.uuid4()}",
                received_at=now,
                subject=f"Recherche publique jobup : {', '.join(result.queries)}",
                alert_label="Premières offres",
                raw_key=key,
                parse_status=ParseStatus.PARSED if offers else ParseStatus.EMPTY,
                parser_version="public-1",
                results_count=len(offers),
            )
            session.add(search)
            await session.flush()
            result.new_offers = await ingest_offers(session, search, Source.JOBUP, offers)
            search.new_offers_count = result.new_offers
        await _save(
            session,
            {
                "status": "done" if result.searches else "failed",
                "at": now.isoformat(),
                "found": result.found,
                "new": result.new_offers,
                "queries": result.queries,
            },
        )
    log.info("first_offers", searches=result.searches, found=result.found, new=result.new_offers)
    return result


# On peut relancer la recherche depuis Alertes, mais pas plus d'une fois par heure.
RELAUNCH_AFTER = timedelta(hours=1)
Requested = Literal["queued", "already_queued", "no_trade", "too_soon"]


async def request(runtime: Runtime, *, first_only: bool = False) -> Requested:
    """Met la recherche en file pour le compte en cours. `first_only` : seulement si elle n'a
    jamais été faite (fin de l'accueil)."""
    async with runtime.sessionmaker.begin() as session:
        current = await state(session)
        if first_only and current:
            return "already_queued"
        at = current.get("at")
        if isinstance(at, str) and datetime.now(UTC) - datetime.fromisoformat(at) < RELAUNCH_AFTER:
            return "too_soon"
        if not await queries(session):
            await _save(session, {**current, "status": "no_trade"})
            return "no_trade"
        await mark_queued(session)

    queued = await enqueue(runtime.settings, "first_offers")
    return "queued" if queued else "already_queued"
