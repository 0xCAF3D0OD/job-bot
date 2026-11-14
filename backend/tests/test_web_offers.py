"""Les premières offres par la recherche web de l'IA (docs/104, « Premières offres par le web »)."""

import json
from collections.abc import AsyncIterator
from datetime import date
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.collect import public_search, web_offers
from jobbot.db.models import AlertSearch, LlmCall, Offer, OfferLink, Search
from jobbot.llm.client import RawResult, WebResult
from jobbot.llm.pricing import Usage
from jobbot.llm.scoring import profile_hash
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring

from .conftest import admin_engine, make_settings

TRUNCATE = "TRUNCATE offers, searches, alert_searches, criteria, llm_calls CASCADE"
ASSC = "https://www.exemple-emploi.ch/offres/assc-123"
CHUV = "https://carrieres.exemple-hopital.ch/job/assc-urgences"
TODAY = date(2026, 11, 14)
# Ce que le moteur a rendu : adresse, titre et, parfois, âge de la page.
RESULTS = (
    WebResult(ASSC, "ASSC en soins à domicile - CMS Exemple | exemple-emploi.ch"),
    WebResult(CHUV, "Un·e ASSC aux urgences, Lausanne", "November 10, 2026"),
    WebResult("https://www.exemple-emploi.ch/emplois?q=assc", "45 emplois ASSC"),
)


def answer(offers: list[dict[str, Any]], urls: tuple[WebResult, ...] = RESULTS) -> RawResult:
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
            {"title": "ASSC en soins à domicile", "company": "CMS Exemple", "url": ASSC},
            # Même adresse, à la barre finale près : une seule offre.
            {"title": "ASSC (doublon)", "url": ASSC + "/"},
            # Inventée : absente des résultats du moteur.
            {"title": "ASSC inventée", "url": "https://www.exemple-emploi.ch/offres/assc-999"},
            {"title": "Sans lien"},
            {"title": "Pas en https", "url": "http://exemple.ch/offre"},
            "n'importe quoi",
        ]
    )
    offers = web_offers.parse_answer(raw, TODAY)
    assert [(o.title, o.company, o.location, o.url) for o in offers] == [
        ("ASSC en soins à domicile", "CMS Exemple", None, ASSC)
    ]
    # Un identifiant à la place de l'intitulé, dans le titre du moteur : écarté.
    code = (WebResult(CHUV, "61d4c807 8a3c 4113 9b3a 6791d579b573"),)
    assert web_offers.parse_answer(answer([{"title": "ASSC", "url": CHUV}], code), TODAY) == []
    # Sans résultat du moteur, ou sans balise : rien, plutôt qu'un lien non vérifié.
    assert web_offers.parse_answer(answer([{"title": "ASSC", "url": ASSC}], ()), TODAY) == []
    silent = RawResult("rien", "m", Usage(1, 0, 0, 1), "end_turn", RESULTS)
    assert web_offers.parse_answer(silent, TODAY) == []


def test_title_company_and_place_are_copied_from_the_engine_never_reworded() -> None:
    """Demande de Kevin (2026-11-14) : titre, entreprise et lieu repris tels quels du résultat
    de recherche. Le code les recopie depuis le titre rendu par le moteur ; ce que l'IA
    propose et qui n'y figure pas mot pour mot est rejeté."""
    shown = "ASSC en soins à domicile - CMS Exemple | exemple-emploi.ch"
    raw = answer(
        [
            {
                # Reformulé par l'IA : le titre du moteur, entier, le remplace.
                "title": "Assistant·e en soins et santé communautaire, soins à domicile",
                # Complété par l'IA (« SA », « Vaud ») : absents du résultat, donc rien.
                "company": "CMS Exemple SA",
                "location": "Lausanne, Vaud",
                "url": ASSC,
            },
            {
                # Un morceau exact du titre du moteur, à la casse près : recopié du moteur.
                "title": "un·e assc aux urgences",
                "company": None,
                "location": "lausanne",
                "url": CHUV,
            },
        ]
    )
    offers = web_offers.parse_answer(raw, TODAY)
    assert [(o.title, o.company, o.location) for o in offers] == [
        (shown, None, None),
        ("Un·e ASSC aux urgences", None, "Lausanne"),
    ]
    # Chaque valeur gardée est un morceau du titre rendu par le moteur.
    titles = {result.url: result.title for result in RESULTS}
    for offer in offers:
        for value in (offer.title, offer.company, offer.location):
            assert value is None or value in titles[offer.url]


def test_offers_older_than_14_days_are_dropped_when_the_date_is_known() -> None:
    def dated(age: str | None) -> RawResult:
        return answer([{"title": "ASSC", "url": ASSC}], (WebResult(ASSC, "ASSC à Nyon", age),))

    for fresh in ("October 31, 2026", "2026-11-01T08:00:00", "3 days ago", "2 weeks ago", "hier"):
        assert len(web_offers.parse_answer(dated(fresh), TODAY)) == 1, fresh
    for old in ("October 30, 2026", "2025-11-12", "15 days ago", "3 weeks ago", "il y a 2 mois"):
        chosen = web_offers.select_offers(dated(old), TODAY)
        assert (chosen.offers, chosen.too_old, chosen.dated) == ([], 1, 1), old
    # Sans date, ou avec une date illisible : gardée, et comptée « sans date ».
    for unknown in (None, "", "bientôt"):
        chosen = web_offers.select_offers(dated(unknown), TODAY)
        assert (len(chosen.offers), chosen.dated, chosen.undated_kept) == (1, 0, 1)
    # La part des résultats datés, affichée par la commande d'essai : 1 sur 3 ici.
    chosen = web_offers.select_offers(answer([]), TODAY)
    assert (chosen.results, chosen.dated) == (3, 1)


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


async def test_web_search_can_be_relaunched_once_a_day_at_most(web: Runtime) -> None:
    """Plafond par compte : la recherche web coûte des appels à l'IA, une relance par jour."""
    from datetime import UTC, datetime, timedelta

    async with web.sessionmaker.begin() as session:
        session.add(AlertSearch(terms="ASSC", location="Lausanne"))
        two_hours_ago = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        await public_search._save(session, {"status": "done", "at": two_hours_ago})
    assert await public_search.request(web) == "too_soon"
    assert public_search.MAX_WEB_QUERIES == 2 and web_offers.MAX_SEARCHES == 2
