"""Les premières offres (docs/104, 0.80.0) : la recherche publique de jobup, une fois."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.collect import public_search
from jobbot.core.filter import Criteria
from jobbot.db.models import AlertSearch, Offer, OfferLink, Search
from jobbot.filtering.service import save_criteria
from jobbot.news import domain
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings

TRUNCATE = "TRUNCATE offers, searches, alert_searches, criteria CASCADE"


def posting(n: int, **extra: Any) -> dict[str, Any]:
    uid = f"00000000-0000-4000-8000-{n:012d}"
    return {
        "@type": "JobPosting",
        "title": f"Menuisier {n} (80-100 %)",
        "description": "Nous recherchons un menuisier.",
        "identifier": {"@type": "PropertyValue", "name": "jobup.ch", "value": uid},
        "hiringOrganization": {"@type": "Organization", "name": f"Atelier {n}"},
        "jobLocation": {"@type": "Place", "address": {"addressLocality": "Sion"}},
        "url": f"https://www.jobup.ch/fr/emplois/detail/{uid}/",
        **extra,
    }


def page(items: list[dict[str, Any]]) -> str:
    data = [
        {"@type": "CollectionPage", "name": "jobs"},
        {
            "@type": "ItemList",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "item": item} for i, item in enumerate(items)
            ],
        },
    ]
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


@pytest.fixture
async def clean() -> AsyncIterator[Runtime]:
    # La recherche est coupée par défaut (0.82.4) : ces tests l'allument.
    runtime = Runtime.create(make_settings(public_search_enabled=True))
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
        await conn.execute(text("DELETE FROM settings WHERE key = 'first_offers'"))
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
        await conn.execute(text("DELETE FROM settings WHERE key = 'first_offers'"))


@pytest.fixture
def no_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(public_search, "DELAY_SECONDS", 0)


def test_postings_and_raw_offers() -> None:
    html = page([posting(1), posting(2, url="https://ailleurs.ch/offre"), {"@type": "Thing"}])
    found = public_search.postings(html)
    assert len(found) == 2
    offers = [o for o in map(public_search.raw_offer, found) if o]
    assert [(o.title, o.company, o.location, o.external_id) for o in offers] == [
        ("Menuisier 1 (80-100 %)", "Atelier 1", "Sion", "00000000-0000-4000-8000-000000000001")
    ]


async def test_queries_from_alerts_or_trade(
    clean: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def keywords(_session: Any, _profile_id: int | None = None) -> list[str]:
        return ["Menuisier", "ébéniste"]

    monkeypatch.setattr(domain, "keywords", keywords)
    async with clean.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(locations=("VS", "Sion", "Sierre", "Martigny")))
    async with clean.sessionmaker() as session:
        # Sans recherche d'alerte : les deux premiers mots, dans les deux premiers lieux (pas
        # les cantons).
        assert await public_search.queries(session) == [
            ("Menuisier", "Sion"),
            ("Menuisier", "Sierre"),
            ("ébéniste", "Sion"),
            ("ébéniste", "Sierre"),
        ]
    async with clean.sessionmaker.begin() as session:
        session.add(AlertSearch(terms="Charpentier", location="Monthey"))
    async with clean.sessionmaker() as session:
        assert await public_search.queries(session) == [("Charpentier", "Monthey")]


async def test_run_first_offers(
    clean: Runtime, monkeypatch: pytest.MonkeyPatch, no_wait: None
) -> None:
    async with clean.sessionmaker.begin() as session:
        session.add(AlertSearch(terms="Menuisier", location="Sion"))
        session.add(AlertSearch(terms="Menuisier", location="Sierre"))
        session.add(AlertSearch(terms="Ébéniste", location="Sion"))
    asked: list[str] = []

    async def fetch(_client: httpx.AsyncClient, url: str) -> str:
        asked.append(url)
        # 10 offres par recherche, dont 2 déjà vues dans la deuxième ; 20 au plus.
        start = {1: 1, 2: 9, 3: 19}[len(asked)]
        return page([posting(n) for n in range(start, start + 10)])

    monkeypatch.setattr(public_search, "fetch", fetch)
    result = await public_search.run_first_offers(clean)
    assert asked == [
        "https://www.jobup.ch/fr/emplois/?term=Menuisier&location=Sion",
        "https://www.jobup.ch/fr/emplois/?term=Menuisier&location=Sierre",
        "https://www.jobup.ch/fr/emplois/?term=%C3%89b%C3%A9niste&location=Sion",
    ]
    # La troisième ne prend que les 2 qui manquent : 20 au plus.
    assert (result.searches, result.found, result.new_offers) == (3, 20, 20)
    async with clean.sessionmaker() as session:
        search = (await session.scalars(select(Search))).one()
        assert search.message_id.startswith("public:") and search.source == "jobup"
        assert search.alert_label == "Premières offres" and search.results_count == 20
        links = list(await session.scalars(select(OfferLink)))
        assert {link.source for link in links} == {"jobup"}
        assert all(link.external_id for link in links)
        assert await session.scalar(select(Offer.id).where(Offer.title == "Menuisier 1 (80-100 %)"))
        state = await public_search.state(session)
    assert state["status"] == "done" and state["new"] == 20
    assert state["queries"] == ["Menuisier · Sion", "Menuisier · Sierre", "Ébéniste · Sion"]
    assert json.loads(clean.storage.get(search.raw_key))["source"] == "jobup"


async def test_failed_search_and_no_trade(
    clean: Runtime, monkeypatch: pytest.MonkeyPatch, no_wait: None
) -> None:
    async def keywords(_session: Any, _profile_id: int | None = None) -> list[str]:
        return []

    monkeypatch.setattr(domain, "keywords", keywords)
    assert (await public_search.run_first_offers(clean)).searches == 0
    async with clean.sessionmaker() as session:
        assert (await public_search.state(session))["status"] == "no_trade"

    async with clean.sessionmaker.begin() as session:
        session.add(AlertSearch(terms="Menuisier", location=None))

    async def blocked(_client: httpx.AsyncClient, url: str) -> str:
        request = httpx.Request("GET", url)
        raise httpx.HTTPStatusError("403", request=request, response=httpx.Response(403))

    monkeypatch.setattr(public_search, "fetch", blocked)
    assert (await public_search.run_first_offers(clean)).searches == 0
    async with clean.sessionmaker() as session:
        assert (await public_search.state(session))["status"] == "failed"
        assert (await session.scalars(select(Search))).first() is None


async def test_public_search_is_not_an_alert(
    clean: Runtime, monkeypatch: pytest.MonkeyPatch, no_wait: None
) -> None:
    async with clean.sessionmaker.begin() as session:
        session.add(AlertSearch(terms="Menuisier", location="Sion"))

    async def fetch(_client: httpx.AsyncClient, url: str) -> str:
        return page([posting(1)])

    monkeypatch.setattr(public_search, "fetch", fetch)
    await public_search.run_first_offers(clean)
    app = create_app(clean.settings, clean)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        # Ni preuve de recherche ORP, ni alerte jobup qui marche.
        month = datetime.now(UTC).strftime("%Y-%m")
        orp = (await api.get("/api/orp", params={"month": month})).json()
        assert orp["searches"] == []
        sites = {s["slug"]: s for s in (await api.get("/api/sites")).json()}
        assert sites["jobup"]["alerts"] == 0
        cells = (await api.get("/api/alert-searches")).json()["searches"][0]["cells"]
        assert [c["status"] for c in cells if c["site"] == "jobup"] == ["todo"]


async def test_request_and_api(clean: Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[str] = []

    async def enqueue(_settings: object, name: str) -> bool:
        queued.append(name)
        return True

    monkeypatch.setattr(public_search, "enqueue", enqueue)
    app = create_app(clean.settings, clean)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        assert (await api.get("/api/alert-searches/first-offers")).json()["status"] == "none"
        async with clean.sessionmaker.begin() as session:
            session.add(AlertSearch(terms="Menuisier", location="Sion"))
        started = await api.post("/api/alert-searches/first-offers")
        assert started.status_code == 202
        assert started.json()["result"] == "queued" and started.json()["status"] == "queued"
        # Faite il y a dix minutes : pas de relance avant une heure.
        async with clean.sessionmaker.begin() as session:
            recent = datetime.now(UTC) - timedelta(minutes=10)
            await public_search._save(session, {"status": "done", "at": recent.isoformat()})
        again = (await api.post("/api/alert-searches/first-offers")).json()
        assert again["result"] == "too_soon" and again["status"] == "done"
    assert queued == ["first_offers"]


async def test_disabled_by_default(runtime: Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    """0.82.4 : les conditions de jobup (déc. 2025, §7) interdisent l'accès automatisé ; la
    recherche est coupée par défaut, sans carte ni relance."""
    queued: list[str] = []

    async def enqueue(_settings: object, name: str) -> bool:
        queued.append(name)
        return True

    async def fetch(_client: httpx.AsyncClient, url: str) -> str:
        raise AssertionError("jobup ne doit pas être lu")

    monkeypatch.setattr(public_search, "enqueue", enqueue)
    monkeypatch.setattr(public_search, "fetch", fetch)
    assert not runtime.settings.public_search_enabled
    assert (await public_search.run_first_offers(runtime)).searches == 0
    app = create_app(runtime.settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        assert (await api.get("/api/alert-searches/first-offers")).json()["status"] == "disabled"
        started = (await api.post("/api/alert-searches/first-offers")).json()
        assert started["result"] == "disabled"
    assert queued == []
