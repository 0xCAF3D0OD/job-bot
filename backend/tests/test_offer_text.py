"""Compléter une offre venue d'une alerte : lire son annonce, ou coller son texte (fiche)."""

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from jobbot import manual_offers
from jobbot.api.app import create_app
from jobbot.db.models import Offer, OfferLink
from jobbot.logos import service as logos
from jobbot.runtime import Runtime
from jobbot.scoring import service

from .test_scoring import FakeClient, add_offer, ai, evaluation, fake  # noqa: F401

LINK = "https://www.exemple-emplois.ch/jobs/view/42"
LONG = "Tu administres nos serveurs Linux et automatises les déploiements avec Ansible. " * 5
POSTING_PAGE = (
    '<html><head><script type="application/ld+json">'
    '{"@type": "JobPosting", "title": "Offre 1", "description": "' + LONG + '"}'
    "</script></head><body>Connexion</body></html>"
)


@pytest.fixture
async def api(ai: Runtime) -> AsyncIterator[AsyncClient]:  # noqa: F811
    app = create_app(ai.settings, ai)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def alert_offer(rt: Runtime, **extra: Any) -> int:
    """Une offre d'alerte, notée sur l'extrait seulement."""
    offer_id = await add_offer(rt, 1, **extra)
    async with rt.sessionmaker.begin() as session:
        session.add(OfferLink(offer_id=offer_id, source="linkedin", external_id="42", url=LINK))
    await service.score_offer(rt, offer_id)
    stored = await evaluation(rt, offer_id)
    assert stored is not None and stored.summary_partial is True
    return offer_id


def site(
    monkeypatch: pytest.MonkeyPatch, robots: str | None, page: str = POSTING_PAGE
) -> list[str]:
    fetched: list[str] = []

    async def fetch_robots(_url: str) -> str | None:
        return robots

    async def fetch_page(url: str) -> str:
        fetched.append(url)
        return page

    monkeypatch.setattr(manual_offers, "fetch_robots", fetch_robots)
    monkeypatch.setattr(manual_offers, "fetch_page", fetch_page)
    return fetched


async def description(rt: Runtime, offer_id: int) -> str | None:
    async with rt.sessionmaker() as session:
        return await session.scalar(select(Offer.description).where(Offer.id == offer_id))


async def test_read_now_fills_the_text_and_rescores(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    offer_id = await alert_offer(ai)
    fetched = site(monkeypatch, "User-agent: *\nDisallow: /admin/\n")

    response = await api.post(f"/api/offers/{offer_id}/read")

    assert response.status_code == 200
    body = response.json()
    assert (body["saved"], body["source"], body["score"], body["problem"]) == (
        True,
        "page",
        78,
        None,
    )
    assert fetched == [LINK]
    assert (await description(ai, offer_id) or "").startswith("Tu administres nos serveurs")
    stored = await evaluation(ai, offer_id)
    assert stored is not None and stored.summary_partial is False
    # La seconde note a lu le texte complet, plus l'extrait.
    assert len(fake.calls) == 2
    assert "texte complet de l'annonce" in str(fake.calls[1]["messages"])


async def test_robots_forbidden_page_is_never_read(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    offer_id = await alert_offer(ai)
    fetched = site(monkeypatch, "User-agent: *\nDisallow: /jobs/\n")

    body = (await api.post(f"/api/offers/{offer_id}/read")).json()

    assert body["saved"] is False and body["paste"] is True
    assert "interdit" in body["problem"] and "colle le texte" in body["problem"]
    assert fetched == []
    assert await description(ai, offer_id) is None
    assert len(fake.calls) == 1


async def test_page_without_announcement_proposes_to_paste(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une page qui demande de se connecter n'a pas d'annonce lisible : on ne force rien."""
    offer_id = await alert_offer(ai)
    site(
        monkeypatch, None, "<html><body><main>Connecte-toi pour voir l'offre.</main></body></html>"
    )

    body = (await api.post(f"/api/offers/{offer_id}/read")).json()

    assert body["saved"] is False and body["paste"] is True
    assert await description(ai, offer_id) is None


async def test_robots_txt_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    async def missing(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        request = httpx.Request("GET", url)
        raise httpx.HTTPStatusError("404", request=request, response=httpx.Response(404))

    monkeypatch.setattr(logos, "_get", missing)
    assert await manual_offers.robots_allowed(LINK) is True

    async def down(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        request = httpx.Request("GET", url)
        raise httpx.HTTPStatusError("503", request=request, response=httpx.Response(503))

    monkeypatch.setattr(logos, "_get", down)
    with pytest.raises(manual_offers.ReadProblem) as closed:
        await manual_offers.robots_allowed(LINK)
    assert closed.value.paste

    async def only_jobA1(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        return b"User-agent: jobA1\nDisallow: /\n\nUser-agent: *\nAllow: /\n", url

    monkeypatch.setattr(logos, "_get", only_jobA1)
    assert await manual_offers.robots_allowed(LINK) is False


async def test_pasted_text_too_short_is_refused(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    offer_id = await alert_offer(ai)

    response = await api.put(
        f"/api/offers/{offer_id}/description", json={"text": "Linux, Ansible.   " * 10}
    )

    assert response.status_code == 422
    assert await description(ai, offer_id) is None


async def test_pasted_text_is_cleaned_and_rescored(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    offer_id = await alert_offer(ai)

    response = await api.put(
        f"/api/offers/{offer_id}/description", json={"text": "  " + LONG.replace(". ", ".\n\n")}
    )

    assert response.status_code == 200
    assert response.json()["source"] == "collé" and response.json()["score"] == 78
    saved = await description(ai, offer_id) or ""
    assert saved == " ".join(LONG.split())
    stored = await evaluation(ai, offer_id)
    assert stored is not None and stored.summary_partial is False


async def test_unknown_offer_and_spontaneous_application(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    assert (await api.post("/api/offers/999999/read")).status_code == 404
    gone = await api.put("/api/offers/999999/description", json={"text": LONG})
    assert gone.status_code == 404
    spontaneous = await add_offer(ai, 2, spontaneous=True)
    assert (await api.post(f"/api/offers/{spontaneous}/read")).status_code == 409
