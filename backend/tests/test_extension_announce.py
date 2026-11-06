"""« Envoyer à jobA1 » depuis l'extension (docs/142 §3) : même lien, même poste chez la même
entreprise (à confirmer), nouvelle offre, limite par jour, texte nettoyé, rien dans le journal."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text
from structlog.testing import capture_logs

from jobbot.api.app import create_app
from jobbot.api.routes import extension as extension_routes
from jobbot.db.models import Evaluation, Offer, OfferLink, Setting
from jobbot.runtime import Runtime
from jobbot.scoring import service

from .conftest import admin_engine
from .test_scoring import FakeClient, ai, fake  # noqa: F401

LINK = "https://www.jobs.ch/fr/offres-emplois/detail/4242/"
BODY = (
    "Tu administres nos serveurs Linux et automatises les déploiements avec Ansible. "
    "Contact : Camille Exemple, RH. "
) * 4


@pytest.fixture(autouse=True)
def fresh_limit() -> None:
    extension_routes.announce_window.hits.clear()


@pytest.fixture
async def api(ai: Runtime) -> AsyncIterator[tuple[AsyncClient, dict[str, str]]]:  # noqa: F811
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE extension_tokens CASCADE"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'identity_name'"))
    async with ai.sessionmaker.begin() as session:
        session.add(Setting(key="identity_name", value="Camille Exemple"))
    app = create_app(ai.settings, ai)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = (await client.post("/api/extension-tokens", json={"name": "Firefox"})).json()
        yield client, {"Authorization": f"Bearer {token['token']}"}


async def alert_offer(rt: Runtime, *, title: str = "Offre 1", company: str = "Sword") -> int:
    """Une offre arrivée par une alerte jobs.ch, notée sur l'extrait seulement."""
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"alerte-{title}",
            title=title,
            company=company,
            first_seen_at=datetime(2026, 10, 30, 8, tzinfo=UTC),
            last_seen_at=datetime(2026, 10, 30, 8, tzinfo=UTC),
            status="to_review",
            snippet="Extrait",
        )
        session.add(offer)
        await session.flush()
        session.add(OfferLink(offer_id=offer.id, source="jobsch", external_id="4242", url=LINK))
        offer_id = offer.id
    await service.score_offer(rt, offer_id)
    return offer_id


def page(**extra: Any) -> dict[str, Any]:
    return {"url": LINK, "title": "Offre 1", "company": "Sword", "text": BODY, **extra}


async def stored(rt: Runtime, offer_id: int) -> Offer:
    async with rt.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None
        return offer


async def offers(rt: Runtime) -> int:
    async with rt.sessionmaker() as session:
        return int(await session.scalar(select(func.count(Offer.id))) or 0)


async def test_same_link_completes_the_offer_and_rescores(
    api: tuple[AsyncClient, dict[str, str]],
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    client, auth = api
    offer_id = await alert_offer(ai)
    # Même lien, écrit autrement (sans www, sans / final) : c'est la même annonce.
    url = "https://jobs.ch/fr/offres-emplois/detail/4242"

    response = await client.post("/api/extension/announce", json=page(url=url), headers=auth)

    assert response.status_code == 200
    body = response.json()
    assert (body["outcome"], body["offer_id"], body["score"], body["label"]) == (
        "filled",
        offer_id,
        78,
        "Proche",
    )
    assert "description" in body["filled"]
    offer = await stored(ai, offer_id)
    assert (offer.description or "").startswith("Tu administres nos serveurs Linux")
    # Renotée tout de suite, sur le texte complet.
    assert len(fake.calls) == 2
    assert "texte complet de l'annonce" in str(fake.calls[1]["messages"])
    async with ai.sessionmaker() as session:
        evaluation = await session.scalar(select(Evaluation).where(Evaluation.offer_id == offer_id))
    assert evaluation is not None and evaluation.summary_partial is False
    assert await offers(ai) == 1


async def test_same_title_and_company_asks_first(
    api: tuple[AsyncClient, dict[str, str]],
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    """Jamais de rattachement silencieux : même poste, même entreprise, autre lien → à confirmer."""
    client, auth = api
    offer_id = await alert_offer(ai)
    other = "https://careers.sword.ch/jobs/offre-1"

    asked = (
        await client.post("/api/extension/announce", json=page(url=other), headers=auth)
    ).json()

    assert asked["outcome"] == "confirm" and asked["offer_id"] is None
    assert asked["known"]["id"] == offer_id
    assert (asked["known"]["title"], asked["known"]["company"], asked["known"]["site"]) == (
        "Offre 1",
        "Sword",
        "jobs.ch",
    )
    assert asked["known"]["received_at"].startswith("2026-10-30")
    assert (await stored(ai, offer_id)).description is None
    assert len(fake.calls) == 1

    # « Oui, compléter cette offre » : l'offre montrée, et elle seule.
    wrong = await client.post(
        "/api/extension/announce",
        json=page(url=other, choice="fill", offer_id=offer_id + 99),
        headers=auth,
    )
    assert wrong.status_code == 409
    yes = (
        await client.post(
            "/api/extension/announce",
            json=page(url=other, choice="fill", offer_id=offer_id),
            headers=auth,
        )
    ).json()
    assert (yes["outcome"], yes["offer_id"], yes["score"]) == ("filled", offer_id, 78)
    assert set(yes["filled"]) == {"description", "url"}
    assert (await stored(ai, offer_id)).description is not None
    assert await offers(ai) == 1


async def test_same_title_and_company_can_be_added_as_new(
    api: tuple[AsyncClient, dict[str, str]],
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    client, auth = api
    offer_id = await alert_offer(ai)

    added = (
        await client.post(
            "/api/extension/announce",
            json=page(url="https://careers.sword.ch/jobs/offre-1", choice="new"),
            headers=auth,
        )
    ).json()

    assert added["outcome"] == "added" and added["offer_id"] != offer_id
    assert added["score"] == 78
    assert await offers(ai) == 2
    assert (await stored(ai, offer_id)).description is None


async def test_unknown_announce_becomes_a_new_offer(
    api: tuple[AsyncClient, dict[str, str]],
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    client, auth = api

    with capture_logs() as logs:
        response = await client.post(
            "/api/extension/announce",
            json=page(url="https://careers.specitec.com/jobs/7", location="Genève"),
            headers=auth,
        )

    body = response.json()
    assert body["outcome"] == "added" and (body["score"], body["label"]) == (78, "Proche")
    offer = await stored(ai, body["offer_id"])
    assert (offer.title, offer.company, offer.location) == ("Offre 1", "Sword", "Genève")
    async with ai.sessionmaker() as session:
        links = list(await session.scalars(select(OfferLink).where(OfferLink.offer_id == offer.id)))
    assert [(link.source, link.url) for link in links] == [
        ("manual", "https://careers.specitec.com/jobs/7")
    ]
    # Le journal : l'id de l'offre et le chemin suivi, jamais le texte (J-1).
    assert any(entry["event"] == "extension_offer_added" for entry in logs)
    assert "Ansible" not in str(logs) and "Camille" not in str(logs)


async def test_text_is_cleaned_like_a_pasted_text(
    api: tuple[AsyncClient, dict[str, str]],
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    """Le nom de la personne retiré, les espaces resserrés, 20 000 caractères au plus."""
    client, auth = api
    long = "  Camille   EXEMPLE\n\n" + BODY + "x" * 30_000

    body = (
        await client.post(
            "/api/extension/announce",
            json=page(url="https://careers.specitec.com/jobs/8", text=long),
            headers=auth,
        )
    ).json()

    description = (await stored(ai, body["offer_id"])).description or ""
    assert description.startswith("[nom retiré] [nom retiré] Tu administres")
    assert "Camille" not in description and "Exemple," not in description
    assert "\n" not in description and "  " not in description
    assert len(description) == 20_000


async def test_page_without_announcement_is_refused(
    api: tuple[AsyncClient, dict[str, str]],
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    client, auth = api
    response = await client.post(
        "/api/extension/announce", json=page(text="Connecte-toi pour voir l'offre."), headers=auth
    )
    assert response.status_code == 422
    assert "annonce" in response.json()["detail"]
    assert await offers(ai) == 0


async def test_thirty_sends_a_day(
    api: tuple[AsyncClient, dict[str, str]],
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    client, auth = api
    await alert_offer(ai)
    for _ in range(30):
        ok = await client.post("/api/extension/announce", json=page(), headers=auth)
        assert ok.status_code == 200
    refused = await client.post("/api/extension/announce", json=page(), headers=auth)
    assert refused.status_code == 429
    assert refused.json()["detail"] == (
        "30 annonces envoyées aujourd'hui : c'est le maximum. Réessaie demain."
    )


async def test_needs_the_extension_token(
    api: tuple[AsyncClient, dict[str, str]],
    ai: Runtime,  # noqa: F811
) -> None:
    client, _auth = api
    response = await client.post("/api/extension/announce", json=page())
    assert response.status_code == 401
