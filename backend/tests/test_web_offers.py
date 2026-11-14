"""Les premières offres par la recherche web de l'IA (docs/104, « Premières offres par le web »)."""

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.collect import public_search, web_offers
from jobbot.db.models import AlertSearch, LlmCall, Offer, OfferLink, Search
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.llm.scoring import profile_hash
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring

from .conftest import admin_engine, make_settings

TRUNCATE = "TRUNCATE offers, searches, alert_searches, criteria, llm_calls CASCADE"
ASSC = "https://www.exemple-emploi.ch/offres/assc-123"
CHUV = "https://carrieres.exemple-hopital.ch/job/assc-urgences"
URLS = (ASSC, CHUV, "https://www.exemple-emploi.ch/emplois?q=assc")


def answer(offers: list[dict[str, Any]], urls: tuple[str, ...] = URLS) -> RawResult:
    body = f"Voici.\n<reponse>{json.dumps({'offers': offers})}</reponse>"
    return RawResult(
        body, web_offers.MODEL, Usage(9000, 0, 0, 600, web_searches=2), "end_turn", urls
    )


class FakeClient:
    def __init__(self, results: list[RawResult]) -> None:
        self.results = results
        self.calls: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.calls.append(params)
        return self.results[len(self.calls) - 1]


@pytest.fixture
async def web() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(
        make_settings(web_first_offers_enabled=True, anthropic_api_key="sk-test")
    )
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
        await conn.execute(text("DELETE FROM settings WHERE key = 'first_offers'"))
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
        await conn.execute(text("DELETE FROM settings WHERE key = 'first_offers'"))
    await runtime.dispose()


def test_request_is_a_web_search_about_the_trade_only() -> None:
    params = web_offers.request_params("ASSC <b>", "Lausanne")
    assert params["tools"][0]["type"].startswith("web_search")
    assert params["tools"][0]["max_uses"] == web_offers.MAX_SEARCHES
    # Seuls le métier et le lieu partent : ni nom, ni adresse, ni CV.
    assert params["messages"][0]["content"] == "<metier>ASSC b</metier>\n<lieu>Lausanne</lieu>"
    assert "Suisse romande" in web_offers.request_params("ASSC", None)["messages"][0]["content"]


def test_only_offers_the_engine_really_returned() -> None:
    raw = answer(
        [
            {"title": "ASSC en soins à domicile", "company": "CMS", "location": None, "url": ASSC},
            # Même adresse, à la barre finale près : une seule offre.
            {"title": "ASSC (doublon)", "url": ASSC + "/"},
            # Inventée : absente des résultats du moteur.
            {"title": "ASSC inventée", "url": "https://www.exemple-emploi.ch/offres/assc-999"},
            # Un identifiant à la place de l'intitulé.
            {"title": "61d4c807 8a3c 4113 9b3a 6791d579b573", "url": CHUV},
            {"title": "Sans lien"},
            {"title": "Pas en https", "url": "http://exemple.ch/offre"},
            "n'importe quoi",
        ]
    )
    offers = web_offers.parse_answer(raw)
    assert [(o.title, o.company, o.location, o.url) for o in offers] == [
        ("ASSC en soins à domicile", "CMS", None, ASSC)
    ]
    # Sans résultat du moteur, ou sans balise : rien, plutôt qu'un lien non vérifié.
    assert web_offers.parse_answer(answer([{"title": "ASSC", "url": ASSC}], ())) == []
    assert (
        web_offers.parse_answer(RawResult("rien", "m", Usage(1, 0, 0, 1), "end_turn", URLS)) == []
    )


async def test_first_offers_by_web_are_listed_but_never_scored(
    web: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with web.sessionmaker.begin() as session:
        session.add(AlertSearch(terms="ASSC", location="Lausanne"))
    fake = FakeClient(
        [
            answer(
                [
                    {"title": "ASSC en soins à domicile", "company": "CMS Exemple", "url": ASSC},
                    {"title": "Un·e ASSC aux urgences", "location": "Lausanne", "url": CHUV},
                ]
            )
        ]
    )
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    assert public_search.provider(web.settings) == "web"
    result = await public_search.run_first_offers(web)
    assert (result.searches, result.found, result.new_offers) == (1, 2, 2)
    assert len(fake.calls) == 1
    async with web.sessionmaker() as session:
        search = (await session.scalars(select(Search))).one()
        assert search.message_id.startswith("public:") and search.source == "web"
        assert search.subject == "Recherche web : ASSC · Lausanne"
        links = list(await session.scalars(select(OfferLink)))
        assert {link.source for link in links} == {"web"}
        assert {link.url for link in links} == {ASSC, CHUV}
        offers = list(await session.scalars(select(Offer)))
        # Ni texte d'annonce, ni note : un intitulé et un lien.
        assert all(o.description is None for o in offers)
        assert (
            await scoring.candidates(session, profile_hash([]), include_stale_profile=False) == []
        )
        call = (await session.scalars(select(LlmCall))).one()
        assert call.purpose == "first_offers"
        state = await public_search.state(session)
    assert state["status"] == "done" and state["provider"] == "web" and state["new"] == 2

    # La liste et la fiche les montrent, sans note, avec leur lien.
    app = create_app(web.settings, web)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        listed = (await api.get("/api/offers")).json()["items"]
        assert {o["title"] for o in listed} == {
            "ASSC en soins à domicile",
            "Un·e ASSC aux urgences",
        }
        assert all(o["score"] is None for o in listed)
        detail = (await api.get(f"/api/offers/{listed[0]['id']}")).json()
        assert [link["source"] for link in detail["links"]] == ["web"]

    # Revue dans une alerte (un lien jobup) : elle se note comme les autres.
    async with web.sessionmaker.begin() as session:
        seen = await session.scalar(select(Offer).where(Offer.title.like("Un·e ASSC%")))
        assert seen is not None
        session.add(OfferLink(offer_id=seen.id, source="jobup", url="https://www.jobup.ch/x"))
    async with web.sessionmaker() as session:
        todo = await scoring.candidates(session, profile_hash([]), include_stale_profile=False)
        assert [o.title for o in todo] == ["Un·e ASSC aux urgences"]


async def test_api_says_where_first_offers_come_from(
    web: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    queued: list[str] = []

    async def enqueue(_settings: object, name: str) -> bool:
        queued.append(name)
        return True

    monkeypatch.setattr(public_search, "enqueue", enqueue)
    app = create_app(web.settings, web)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        first = (await api.get("/api/alert-searches/first-offers")).json()
        assert (first["status"], first["provider"]) == ("none", "web")
        async with web.sessionmaker.begin() as session:
            session.add(AlertSearch(terms="ASSC", location="Lausanne"))
        started = (await api.post("/api/alert-searches/first-offers")).json()
        assert (started["result"], started["provider"]) == ("queued", "web")
    assert queued == ["first_offers"]


async def test_web_needs_the_setting_and_an_ai_key(runtime: Runtime) -> None:
    assert public_search.provider(runtime.settings) is None
    assert public_search.provider(make_settings(web_first_offers_enabled=True)) is None
    both = make_settings(
        web_first_offers_enabled=True, public_search_enabled=True, anthropic_api_key="sk-test"
    )
    assert public_search.provider(both) == "jobup"
