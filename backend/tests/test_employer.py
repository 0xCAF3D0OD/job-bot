"""Voir l'offre chez l'employeur (docs/20 §2). Sans réseau."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import Company, Evaluation, LlmCall, Offer, OfferStatus
from jobbot.employer import service
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.logos import service as logos
from jobbot.registry.service import name_key
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring
from jobbot.worker.jobs import execute

from .conftest import make_settings

NOW = datetime(2026, 10, 7, 8, 0, tzinfo=UTC)
HOME = b'<html><a href="/fr/carrieres">Carri\xc3\xa8res</a></html>'
CAREERS = b'<html><iframe src="https://boards.greenhouse.io/embed/job_board?for=exemplesa"></iframe></html>'
BOARD = json.dumps(
    {
        "jobs": [
            {
                "title": "Comptable",
                "absolute_url": "https://job-boards.greenhouse.io/exemplesa/jobs/1",
            },
            {
                "title": "Ingénieur DevOps (H/F) 100%",
                "absolute_url": "https://job-boards.greenhouse.io/exemplesa/jobs/2",
            },
        ]
    }
).encode()
EMPLOYER_PAGE = (
    "<html><h1>Ingénieur DevOps</h1><p>Exemple SA recrute à Lausanne.</p></html>".encode()
)


class FakeClient:
    def __init__(self, text_: str) -> None:
        self.text = text_
        self.calls: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.calls.append(params)
        return RawResult(
            self.text, service.MODEL, Usage(2000, 0, 0, 200, web_searches=2), "end_turn"
        )


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(anthropic_api_key="sk-test"))
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, companies, llm_calls CASCADE"))
    yield runtime
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, companies, llm_calls CASCADE"))
    await runtime.dispose()


async def add_offer(rt: Runtime, n: int, score: int = 80, **extra: Any) -> int:
    async with rt.sessionmaker.begin() as session:
        values: dict[str, Any] = {"company": "Exemple SA", **extra}
        offer = Offer(
            fingerprint=f"e{n}",
            title="Ingénieur DevOps (H/F)",
            location="Lausanne",
            first_seen_at=NOW,
            last_seen_at=NOW,
            status=OfferStatus.TO_REVIEW,
            **values,
        )
        session.add(offer)
        await session.flush()
        session.add(
            Evaluation(offer_id=offer.id, filter_passed=True, criteria_hash="x", score=score)
        )
        return offer.id


def test_matching_rules() -> None:
    assert service.title_matches("Ingénieur DevOps (H/F)", "Ingenieur devops - 80-100%")
    assert not service.title_matches("Ingénieur DevOps", "Comptable")
    assert service.is_agency("Adecco Human Resources", None)
    assert service.is_agency("Exemple SA", "Pour notre client, une PME vaudoise…")
    assert not service.is_agency("Exemple SA", "Rejoignez notre équipe")
    assert service.detect_ats('<a href="https://jobs.lever.co/exemple">') == "lever:exemple"
    assert service.detect_ats('src="https://exemple.jobs.personio.de/"') == "personio:exemple"
    assert (
        service.careers_link('<a href="/jobs">Jobs</a>', "https://exemple.ch/")
        == "https://exemple.ch/jobs"
    )
    assert service.is_proxy("https://www.jobup.ch/fr/emplois/detail/1/")
    assert (
        service.parse_answer(
            '<reponse>{"found": true, "url": "https://exemple.ch/job/2"}</reponse>'
        )
        == "https://exemple.ch/job/2"
    )
    assert service.parse_answer('<reponse>{"found": false}</reponse>') is None


async def test_found_through_the_recruiting_tool(
    rt: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    pages = {
        "https://exemple.ch/": HOME,
        "https://exemple.ch/fr/carrieres": CAREERS,
        "https://boards-api.greenhouse.io/v1/boards/exemplesa/jobs": BOARD,
    }

    async def fake_get(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        if url in pages:
            return pages[url], url
        raise logos.Refused("inconnu")

    monkeypatch.setattr(logos, "_get", fake_get)
    offer_id = await add_offer(rt, 1, company_website="https://exemple.ch/a-propos")
    result = await service.find(rt, offer_id, use_web=False)
    assert result == service.Found(
        "https://job-boards.greenhouse.io/exemplesa/jobs/2", "ats", "found"
    )
    async with rt.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        company = await session.get(Company, name_key("Exemple SA"))
    assert offer is not None and offer.employer_url_source == "ats" and offer.employer_checked_at
    assert company is not None and company.ats == "greenhouse:exemplesa"


async def test_web_search_verified_then_not_found(
    rt: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_get(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        if url == "https://exemple.ch/emplois/devops":
            return EMPLOYER_PAGE, url
        raise logos.Refused("inconnu")

    monkeypatch.setattr(logos, "_get", fake_get)
    fake = FakeClient(
        '<reponse>{"found": true, "url": "https://exemple.ch/emplois/devops"}</reponse>'
    )
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    offer_id = await add_offer(rt, 2)
    assert (await service.find(rt, offer_id)) == service.Found(
        "https://exemple.ch/emplois/devops", "web", "found"
    )
    assert "<entreprise>Exemple SA</entreprise>" in fake.calls[0]["messages"][0]["content"]

    # Page sans le titre, ou plateforme d'annonces : refusée.
    fake.text = (
        '<reponse>{"found": true, "url": "https://www.jobup.ch/fr/emplois/detail/9/"}</reponse>'
    )
    other = await add_offer(rt, 3)
    assert (await service.find(rt, other)) == service.Found(None, None, "not_found")
    async with rt.sessionmaker() as session:
        purposes = list(await session.scalars(select(LlmCall.purpose)))
    assert purposes == ["employer", "employer"]


async def test_agency_and_known_link(rt: Runtime) -> None:
    agency = await add_offer(rt, 4, company="Manpower SA")
    assert (await service.find(rt, agency)) == service.Found(None, None, "agency")
    known = await add_offer(rt, 5, apply_kind="external", apply_url="https://exemple.ch/postuler")
    assert await service.find(rt, known) is None  # lien employeur déjà connu par jobup


async def test_job_and_endpoint(rt: Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    async def refuse(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        raise logos.Refused("hors ligne")

    monkeypatch.setattr(logos, "_get", refuse)
    fake = FakeClient('<reponse>{"found": false}</reponse>')
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    high = await add_offer(rt, 6, score=85)
    low = await add_offer(rt, 7, score=40)
    assert await execute(rt, "employer") is True
    async with rt.sessionmaker() as session:
        statuses = {o.id: o.employer_status for o in await session.scalars(select(Offer))}
    assert statuses[high] == "not_found" and statuses[low] is None  # sous le seuil de 70

    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        response = await api.post(f"/api/offers/{low}/employer")
        assert response.status_code == 200 and response.json()["employer_status"] == "not_found"
        assert (await api.post("/api/offers/999999/employer")).status_code == 404
