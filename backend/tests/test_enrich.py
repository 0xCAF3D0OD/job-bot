"""Lecture des pages d'offres jobup : analyse de la page et tâche enrich (sans réseau)."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select, text, update

from jobbot.db.models import Offer, OfferLink, OfferStatus
from jobbot.enrich import service
from jobbot.enrich.service import FetchResult
from jobbot.runtime import Runtime
from jobbot.sources.jobup_page import ApplyKind, PageNotParsable, parse_jobup_page

PAGES = Path(__file__).parent / "fixtures" / "pages"
UUID = "f322e247-a189-40ed-86f6-0a9ed911b321"
URL = f"https://www.jobup.ch/fr/emplois/detail/{UUID}/"
NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)


def page(name: str) -> str:
    return (PAGES / name).read_text(encoding="utf-8")


# --- Analyse de la page ---------------------------------------------------------------


def test_external_application() -> None:
    parsed = parse_jobup_page(page("jobup-externe.html"), URL)
    assert parsed.apply_kind is ApplyKind.EXTERNAL
    assert parsed.apply_url == "https://www.aplitrak.com/?adid=x"
    assert parsed.employment_type == "Temporaire"
    assert parsed.description and parsed.description.startswith("Notre client recherche")
    assert "<" not in parsed.description


def test_jobup_form() -> None:
    parsed = parse_jobup_page(page("jobup-formulaire.html"), URL)
    assert (parsed.apply_kind, parsed.apply_url) == (ApplyKind.JOBUP, URL)
    assert parsed.employment_type == "Durée indéterminée"
    assert parsed.description and parsed.description.startswith("Kinnarps")


def test_jobup_form_when_method_is_not_external() -> None:
    html = page("jobup-externe.html").replace(
        "APPLICATION_METHOD.EXTERNAL", "APPLICATION_METHOD.ONLINE"
    )
    parsed = parse_jobup_page(html, URL)
    assert (parsed.apply_kind, parsed.apply_url) == (ApplyKind.JOBUP, URL)


def test_external_without_url_falls_back_to_jobup() -> None:
    html = page("jobup-externe.html").replace(
        '"externalUrl":"https:\\u002F\\u002Fwww.aplitrak.com\\u002F?adid=x"', '"externalUrl":""'
    )
    assert parse_jobup_page(html, URL).apply_kind is ApplyKind.JOBUP


def test_page_without_offer_is_rejected() -> None:
    with pytest.raises(PageNotParsable):
        parse_jobup_page("<html><body>Erreur</body></html>", URL)


# --- Tâche enrich ---------------------------------------------------------------------


class FakeWeb:
    def __init__(self) -> None:
        self.responses: dict[str, FetchResult | Exception] = {}
        self.calls: list[str] = []
        self.sleeps: list[float] = []

    async def fetch(self, url: str) -> FetchResult:
        self.calls.append(url)
        response = self.responses.get(url, FetchResult(200, page("jobup-externe.html"), url))
        if isinstance(response, Exception):
            raise response
        return response

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)


@pytest.fixture
def web(monkeypatch: pytest.MonkeyPatch) -> FakeWeb:
    fake = FakeWeb()
    monkeypatch.setattr(service, "fetch", fake.fetch)
    monkeypatch.setattr(service, "sleep", fake.sleep)
    return fake


@pytest.fixture
async def fresh(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, searches, job_runs CASCADE"))
    yield runtime


async def add(
    runtime: Runtime,
    n: int,
    *,
    source: str = "jobup",
    status: str = OfferStatus.TO_REVIEW,
    url: str | None = None,
) -> int:
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"offre-{n}",
            title=f"Offre {n}",
            first_seen_at=NOW + timedelta(minutes=n),
            last_seen_at=NOW,
            status=status,
        )
        session.add(offer)
        await session.flush()
        link = url or f"https://www.jobup.ch/fr/emplois/detail/{n:08d}-0000-4000-8000-000000000000/"
        session.add(OfferLink(offer_id=offer.id, source=source, url=link))
        return offer.id


async def get(runtime: Runtime, offer_id: int) -> Offer:
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None
        return offer


async def test_enrich_reads_only_eligible_offers_slowly(fresh: Runtime, web: FakeWeb) -> None:
    first = await add(fresh, 1)
    second = await add(fresh, 2)
    indeed = await add(fresh, 3, source="indeed", url="https://ch.indeed.com/viewjob?jk=k")
    filtered = await add(fresh, 4, status=OfferStatus.FILTERED_OUT)
    later = await add(fresh, 5, status=OfferStatus.LATER)

    result = await service.enrich(fresh)

    assert (result.fetched, result.ok) == (2, 2)
    assert len(web.calls) == 2 and all(c.startswith("https://www.jobup.ch/") for c in web.calls)
    assert web.sleeps == [10.0]  # une pause entre deux requêtes
    done = await get(fresh, second)
    assert (done.enrich_status, done.apply_kind, done.enrich_attempts) == ("ok", "external", 1)
    assert done.apply_url == "https://www.aplitrak.com/?adid=x"
    assert (await get(fresh, first)).description
    assert (await get(fresh, indeed)).enrich_status == "skipped"
    assert (await get(fresh, filtered)).enrich_status == "pending"
    assert (await get(fresh, later)).enrich_status == "pending"

    again = await service.enrich(fresh)
    assert again.fetched == 0  # une seule lecture par offre


async def test_enrich_caps_requests_per_run(
    fresh: Runtime, web: FakeWeb, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(service, "MAX_PER_RUN", 3)
    for n in range(1, 6):
        await add(fresh, n)
    assert (await service.enrich(fresh)).fetched == 3
    assert (await service.enrich(fresh)).fetched == 2


async def test_enrich_refuses_unexpected_urls(fresh: Runtime, web: FakeWeb) -> None:
    offer = await add(fresh, 1, url="https://www.jobup.ch/fr/external/abc/")
    assert (await service.enrich(fresh)).fetched == 0
    assert web.calls == []
    assert (await get(fresh, offer)).enrich_status == "skipped"


async def test_expired_failed_and_retry(fresh: Runtime, web: FakeWeb) -> None:
    gone = await add(fresh, 1)
    broken = await add(fresh, 2)
    down = await add(fresh, 3)
    async with fresh.sessionmaker() as session:
        links = {link.offer_id: link.url for link in await session.scalars(select(OfferLink))}
    web.responses[links[gone]] = FetchResult(404, "", links[gone])
    web.responses[links[broken]] = FetchResult(200, "<html></html>", links[broken])
    web.responses[links[down]] = httpx.ConnectTimeout("délai dépassé")

    result = await service.enrich(fresh)
    assert (result.expired, result.failed) == (1, 2)
    assert (await get(fresh, gone)).enrich_status == "expired"
    assert (await get(fresh, broken)).enrich_status == "failed"

    # Pas de nouvel essai avant un jour…
    assert (await service.enrich(fresh)).fetched == 0
    # … puis au plus trois essais en tout.
    async with fresh.sessionmaker.begin() as session:
        await session.execute(update(Offer).values(enriched_at=NOW - timedelta(days=2)))
    assert (await service.enrich(fresh)).fetched == 2
    async with fresh.sessionmaker.begin() as session:
        await session.execute(
            update(Offer).values(enriched_at=NOW - timedelta(days=2), enrich_attempts=3)
        )
    assert (await service.enrich(fresh)).fetched == 0


async def test_description_feeds_the_filter(fresh: Runtime, web: FakeWeb) -> None:
    from jobbot.core.filter import ContractType, Criteria
    from jobbot.filtering.service import run_filter, save_criteria

    offer = await add(fresh, 1)
    async with fresh.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(excluded_types=(ContractType.TEMPORARY,)))
    await run_filter(fresh)
    assert (await get(fresh, offer)).status == "to_review"
    await service.enrich(fresh)  # la page indique « Temporaire »
    await run_filter(fresh)
    assert (await get(fresh, offer)).status == "filtered_out"


# --- Adresse du lieu de travail (docs/12 §2.1) ------------------------------------------

LOCATION = (
    '"jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress",'
    ' "streetAddress": "Chemin de l\'Exemple  10", "addressRegion": "Genève",'
    ' "postalCode": "1206", "addressCountry": "CH"}}, "employmentType"'
)


def page_with_address() -> str:
    return page("jobup-externe.html").replace('"employmentType"', LOCATION, 1)


def test_address_from_job_location() -> None:
    assert (
        parse_jobup_page(page_with_address(), URL).address == "Chemin de l'Exemple 10\n1206 Genève"
    )
    assert parse_jobup_page(page("jobup-externe.html"), URL).address is None


def url(n: int) -> str:
    return f"https://www.jobup.ch/fr/emplois/detail/{n:08d}-0000-4000-8000-000000000000/"


async def test_enrich_and_recheck_store_address(fresh: Runtime, web: FakeWeb) -> None:
    new = await add(fresh, 1)
    manual = await add(fresh, 2)
    old = await add(fresh, 3)
    for n in (1, 2, 3):
        web.responses[url(n)] = FetchResult(200, page_with_address(), url(n))
    async with fresh.sessionmaker.begin() as session:
        await session.execute(
            update(Offer)
            .where(Offer.id == manual)
            .values(company_address="Rue saisie 1\n1000 Lausanne", company_address_source="manual")
        )
        await session.execute(
            update(Offer)
            .where(Offer.id == old)
            .values(enrich_status="ok", enriched_at=datetime.now(UTC) - timedelta(days=4))
        )
    await service.enrich(fresh)
    assert ((await get(fresh, new)).company_address_source) == "page"
    assert (await get(fresh, manual)).company_address == "Rue saisie 1\n1000 Lausanne"
    # Lue avant 0.7.1 : l'adresse arrive à la revérification.
    rechecked = await get(fresh, old)
    assert (rechecked.company_address, rechecked.company_address_source) == (
        "Chemin de l'Exemple 10\n1206 Genève",
        "page",
    )
