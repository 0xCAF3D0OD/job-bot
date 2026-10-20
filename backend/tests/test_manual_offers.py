"""Ajouter une offre trouvée ailleurs (docs/111) : lien ou texte, fiche à relire, puis l'offre."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot import manual_offers
from jobbot.api.app import create_app
from jobbot.core.filter import Criteria
from jobbot.db.models import LlmCall, Offer, OfferLink
from jobbot.enrich.service import expire_stale
from jobbot.filtering.service import save_criteria
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.logos import service as logos
from jobbot.news import domain
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring

from .conftest import admin_engine, make_settings

TRUNCATE = "TRUNCATE offers, criteria, llm_calls CASCADE"

POSTING_PAGE = """<html><head>
<script type="application/ld+json">{"@context": "https://schema.org", "@graph": [
  {"@type": "WebPage", "name": "Carrières"},
  {"@type": ["JobPosting"], "title": "Développeuse Full Stack (80-100 %)",
   "hiringOrganization": {"@type": "Organization", "name": "Exemple SA"},
   "jobLocation": [{"@type": "Place", "address": {"addressLocality": "Lausanne"}}],
   "description": "&lt;p&gt;Tu développes nos applications.&lt;br&gt;Vue et Python.&lt;/p&gt;"}
]}</script></head><body>Annonce</body></html>"""

PLAIN_PAGE = (
    "<html><body><main>" + "Nous cherchons un menuisier qualifié. " * 10 + "</main></body></html>"
)


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.calls.append(params)
        body = {
            "offers": [
                {
                    "title": "Menuisier CFC",
                    "company": "Bois & Fils",
                    "location": "Sion",
                    "rate": "100 %",
                    "link": 1,
                }
            ]
        }
        return RawResult(
            json.dumps(body), "claude-haiku-4-5-20251001", Usage(2000, 0, 0, 100), "end_turn"
        )


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(anthropic_api_key="sk-test"))
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
    await runtime.dispose()


@pytest.fixture
async def api(rt: Runtime) -> AsyncIterator[AsyncClient]:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def trade(monkeypatch: pytest.MonkeyPatch) -> None:
    async def keywords(_session: Any, _profile_id: int | None = None) -> list[str]:
        return ["Développeur web", "Vue"]

    monkeypatch.setattr(domain, "keywords", keywords)


@pytest.fixture
def ai(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    fake = FakeClient()
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    return fake


def page(monkeypatch: pytest.MonkeyPatch, body: str) -> None:
    async def fetch(_url: str) -> str:
        return body

    monkeypatch.setattr(manual_offers, "fetch_page", fetch)


def test_job_posting_forms() -> None:
    graph = manual_offers.job_posting(POSTING_PAGE)
    assert graph is not None and graph["title"].startswith("Développeuse")
    listed = '<script type="application/ld+json">[{"@type": "JobPosting", "title": "A"}]</script>'
    assert manual_offers.job_posting(listed) == {"@type": "JobPosting", "title": "A"}
    assert manual_offers.job_posting("<script type='x'>{}</script><p>rien</p>") is None
    draft = manual_offers.draft_from_posting(graph, "https://exemple.ch/job/1")
    assert draft is not None
    assert (draft.company, draft.location, draft.read_by) == ("Exemple SA", "Lausanne", "page")
    assert draft.description == "Tu développes nos applications.\nVue et Python."


def test_about_trade() -> None:
    words = ["Développeur web"]
    assert manual_offers.about_trade(words, "Développeuse Full Stack")
    assert manual_offers.about_trade(["Entwickler"], "Entwicklerin Frontend")
    assert not manual_offers.about_trade(words, "Menuisier CFC", "Travail du bois")


async def test_private_and_protected_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    for url in ("http://exemple.ch/annonce", "https://localhost/annonce", "https://127.0.0.1/a"):
        with pytest.raises(manual_offers.ReadProblem) as refused:
            await manual_offers.fetch_page(url)
        assert refused.value.message.startswith("Lien refusé") and not refused.value.paste

    async def blocked(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        request = httpx.Request("GET", url)
        raise httpx.HTTPStatusError("403", request=request, response=httpx.Response(403))

    monkeypatch.setattr(logos, "_get", blocked)
    with pytest.raises(manual_offers.ReadProblem) as protected:
        await manual_offers.fetch_page("https://ch.indeed.com/viewjob?jk=1")
    assert protected.value.paste and "colle le texte" in protected.value.message


async def test_read_link_with_posting_then_add(
    api: AsyncClient, rt: Runtime, monkeypatch: pytest.MonkeyPatch, trade: None, ai: FakeClient
) -> None:
    page(monkeypatch, POSTING_PAGE)
    read = (await api.post("/api/offers/manual/read", json={"url": "exemple.ch/job/1"})).json()
    draft = read["draft"]
    assert draft["read_by"] == "page" and draft["url"] == "https://exemple.ch/job/1"
    assert (draft["trade"], draft["matches_trade"], draft["existing_offer_id"]) == (
        "Développeur web",
        True,
        None,
    )
    assert ai.calls == []  # le balisage suffit : pas d'IA

    added = await api.post("/api/offers/manual", json={**draft, "location": "Lausanne"})
    assert added.status_code == 201
    body = added.json()
    assert body["existing"] is False and body["status"] in ("new", "to_review")
    async with rt.sessionmaker() as session:
        offer = await session.get(Offer, body["id"])
        assert offer is not None
        assert (offer.company, offer.location) == ("Exemple SA", "Lausanne")
        links = list(await session.scalars(select(OfferLink).where(OfferLink.offer_id == offer.id)))
        assert [(link.source, link.url) for link in links] == [
            ("manual", "https://exemple.ch/job/1")
        ]
        # Notée comme les autres.
        candidates = await scoring.candidates(session, "h", include_stale_profile=False)
        assert offer.id in {o.id for o in candidates}

    # Même lien : la fiche le signale, l'ajout ouvre celle qui existe.
    again = (await api.post("/api/offers/manual/read", json={"url": "exemple.ch/job/1"})).json()
    assert again["draft"]["existing_offer_id"] == body["id"]
    twice = (await api.post("/api/offers/manual", json=draft)).json()
    assert twice == {**twice, "id": body["id"], "existing": True}
    context = (await api.get("/api/offers/manual")).json()
    assert context == {"trade": "Développeur web", "added_today": 1, "daily_limit": 20}

    # Jamais expirée faute d'alerte.
    async with rt.sessionmaker.begin() as session:
        offer = await session.get(Offer, body["id"])
        assert offer is not None
        offer.last_seen_at = offer.last_seen_at.replace(year=offer.last_seen_at.year - 1)
    assert await expire_stale(rt, offer.first_seen_at) == 0


async def test_read_page_or_text_with_ai(
    api: AsyncClient, rt: Runtime, monkeypatch: pytest.MonkeyPatch, trade: None, ai: FakeClient
) -> None:
    page(monkeypatch, PLAIN_PAGE)
    draft = (
        await api.post("/api/offers/manual/read", json={"url": "https://bois.ch/emploi"})
    ).json()["draft"]
    assert (draft["title"], draft["company"], draft["read_by"]) == (
        "Menuisier CFC",
        "Bois & Fils",
        "ia",
    )
    assert draft["location"] == "Sion 100 %"
    # Le métier n'y est pas : la fiche le dit.
    assert draft["matches_trade"] is False

    pasted = "Menuisier CFC chez Bois & Fils à Sion. Contact : jean@bois.ch, 079 123 45 67."
    text_read = (await api.post("/api/offers/manual/read", json={"text": pasted})).json()
    assert text_read["draft"]["url"] is None
    sent = ai.calls[-1]["messages"][0]["content"]
    assert "jean@bois.ch" not in json.dumps(sent)
    async with rt.sessionmaker() as session:
        purposes = list(await session.scalars(select(LlmCall.purpose)))
    assert purposes == ["manual_offer", "manual_offer"]

    empty = (await api.post("/api/offers/manual/read", json={"text": "  "})).json()
    assert empty["draft"] is None and empty["problem"]


async def test_page_without_offer_asks_for_text(
    api: AsyncClient, monkeypatch: pytest.MonkeyPatch, ai: FakeClient
) -> None:
    page(monkeypatch, "<html><body>Connexion requise</body></html>")
    out = (await api.post("/api/offers/manual/read", json={"url": "https://x.ch/a"})).json()
    assert out["draft"] is None and out["paste"] is True and ai.calls == []


async def test_filtered_out_offer_is_kept_with_reason(api: AsyncClient, rt: Runtime) -> None:
    async with rt.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(banned_words=("menuisier",)))
    added = (
        await api.post(
            "/api/offers/manual",
            json={"title": "Menuisier CFC", "company": "Bois & Fils", "location": "Sion"},
        )
    ).json()
    assert added["status"] == "filtered_out" and added["reasons"]
    # Ajoutée par son texte : l'étiquette, et aucun lien vide à ouvrir.
    offer = (await api.get(f"/api/offers/{added['id']}")).json()
    assert offer["added_by_you"] is True and offer["links"] == []
    prefill = (await api.get(f"/api/offers/{added['id']}/application-prefill")).json()
    assert prefill["application_url"] is None


async def test_link_goes_to_orp_line(api: AsyncClient) -> None:
    added = (
        await api.post(
            "/api/offers/manual",
            json={"title": "Développeur web", "url": "https://exemple.ch/job/2"},
        )
    ).json()
    offer = (await api.get(f"/api/offers/{added['id']}")).json()
    assert offer["links"] == [{**offer["links"][0], "source": "manual"}]
    prefill = (await api.get(f"/api/offers/{added['id']}/application-prefill")).json()
    assert prefill["application_url"] == "https://exemple.ch/job/2"


async def test_daily_limit(api: AsyncClient) -> None:
    for i in range(manual_offers.DAILY_LIMIT):
        created = await api.post("/api/offers/manual", json={"title": f"Poste {i}"})
        assert created.status_code == 201
    refused = await api.post("/api/offers/manual", json={"title": "Un de trop"})
    assert refused.status_code == 429
    assert "20 offres" in refused.json()["detail"]
