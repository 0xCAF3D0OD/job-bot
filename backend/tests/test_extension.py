"""Extension du navigateur (docs/25) : jetons, offre reconnue, données, « J'ai envoyé »."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import Application, Draft, LlmCall, Offer, OfferLink
from jobbot.extension import service
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring

from .conftest import make_settings


@pytest.fixture
async def secured() -> AsyncIterator[AsyncClient]:
    """API avec connexion obligatoire : l'extension passe par son jeton seulement."""
    runtime = Runtime.create(make_settings(auth_enabled=True))
    app = create_app(runtime.settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await runtime.dispose()


async def reset(runtime: Runtime) -> None:
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE extension_tokens, offers, applications, llm_calls CASCADE")
        )
        await conn.execute(
            text("DELETE FROM settings WHERE key LIKE 'identity_%' OR key LIKE 'apply_%'")
        )


async def add_offer(runtime: Runtime, **values: object) -> int:
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"ext-{values.get('title', 'SRE')}",
            status="preparing",
            first_seen_at=now,
            last_seen_at=now,
            **{"title": "SRE", "company": "Exemple SA", **values},
        )
        session.add(offer)
        await session.flush()
        session.add(
            Draft(
                offer_id=offer.id,
                kind="letter",
                version=1,
                language="fr",
                content={
                    "subject": "Candidature",
                    "paragraphs": [{"text": "Motivé.", "chunk_ids": []}],
                },
            )
        )
        return offer.id


def test_same_page() -> None:
    known = "https://boards.greenhouse.io/exemple/jobs/123"
    assert service.same_page("https://boards.greenhouse.io/exemple/jobs/123/apply?x=1", known)
    assert service.same_page("http://www.boards.greenhouse.io/exemple/jobs/123/", known)
    assert not service.same_page("https://boards.greenhouse.io/exemple/jobs/1234", known)
    assert not service.same_page("https://autre.ch/exemple/jobs/123", known)
    assert not service.same_page("https://boards.greenhouse.io/", "https://boards.greenhouse.io/")
    assert not service.same_page("javascript:alert(1)", known)


async def test_tokens_and_extension_routes(
    client: AsyncClient, secured: AsyncClient, runtime: Runtime
) -> None:
    await reset(runtime)
    # Sans jeton (ni avec un faux), rien, même sans connexion obligatoire.
    assert (await client.get("/api/extension/me")).status_code == 401
    bad = {"Authorization": "Bearer jbx_faux"}
    assert (await client.get("/api/extension/me", headers=bad)).status_code == 401

    created = (await client.post("/api/extension-tokens", json={"name": "Chrome"})).json()
    token = created["token"]
    assert token.startswith("jbx_") and created["name"] == "Chrome"
    listed = (await client.get("/api/extension-tokens")).json()
    assert [t["id"] for t in listed] == [created["id"]] and "token" not in listed[0]
    auth = {"Authorization": f"Bearer {token}"}

    # Le jeton suffit, même quand la connexion est obligatoire (pas de cookie)…
    assert (await secured.get("/api/extension/me", headers=auth)).json()["platform"] == "job-bot"
    # … et ne donne accès qu'aux routes de l'extension.
    assert (await secured.get("/api/offers", headers=auth)).status_code == 401
    # Une requête venue d'une extension (autre origine) passe : le jeton remplace le cookie.
    cross = {**auth, "Origin": "chrome-extension://abc", "Sec-Fetch-Site": "cross-site"}
    assert (await secured.get("/api/extension/me", headers=cross)).status_code == 200

    revoked = await client.delete(f"/api/extension-tokens/{created['id']}")
    assert revoked.status_code == 204
    assert (await client.get("/api/extension/me", headers=auth)).status_code == 401
    assert (await client.get("/api/extension-tokens")).json() == []
    await reset(runtime)


async def test_match_fill_and_sent(client: AsyncClient, runtime: Runtime) -> None:
    await reset(runtime)
    form = "https://jobs.lever.co/exemple/abc-123"
    offer_id = await add_offer(runtime, employer_url=form)
    other = await add_offer(runtime, title="DevOps")
    async with runtime.sessionmaker.begin() as session:
        session.add(
            OfferLink(
                offer_id=other, source="jobup", url="https://www.jobup.ch/fr/emplois/detail/42/"
            )
        )
    await client.put(
        "/api/identity",
        json={"name": "Camille Exemple", "email": "camille@example.ch", "permit": "Permis C"},
    )
    token = (await client.post("/api/extension-tokens", json={})).json()["token"]
    auth = {"Authorization": f"Bearer {token}"}

    matched = (
        await client.get("/api/extension/match", params={"url": form + "/apply"}, headers=auth)
    ).json()
    assert matched["offer"]["id"] == offer_id
    assert {c["id"] for c in matched["choices"]} == {offer_id, other}
    by_link = (
        await client.get(
            "/api/extension/match",
            params={"url": "https://jobup.ch/fr/emplois/detail/42"},
            headers=auth,
        )
    ).json()
    assert by_link["offer"]["id"] == other
    unknown = (
        await client.get(
            "/api/extension/match", params={"url": "https://ailleurs.ch/x"}, headers=auth
        )
    ).json()
    assert unknown["offer"] is None and len(unknown["choices"]) == 2

    data = (await client.get(f"/api/extension/offers/{offer_id}", headers=auth)).json()
    assert (
        data["identity"]["name"] == "Camille Exemple" and data["identity"]["permit"] == "Permis C"
    )
    assert data["letter_text"] == "Motivé." and data["has_letter"] and not data["has_cv"]
    assert data["letter_filename"] == "Lettre - Exemple SA.pdf"
    pdf = await client.get(f"/api/extension/offers/{offer_id}/letter.pdf", headers=auth)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert (
        await client.get(f"/api/extension/offers/{offer_id}/cv.pdf", headers=auth)
    ).status_code == 404

    sent = await client.post(
        f"/api/extension/offers/{offer_id}/sent", json={"url": form + "/apply"}, headers=auth
    )
    assert sent.status_code == 200
    again = await client.post(f"/api/extension/offers/{offer_id}/sent", json={}, headers=auth)
    assert again.json()["application_id"] == sent.json()["application_id"]
    async with runtime.sessionmaker() as session:
        application = await session.scalar(
            select(Application).where(Application.offer_id == offer_id)
        )
        assert application is not None and application.application_url == form + "/apply"
        assert (await session.get(Offer, offer_id)).status == "applied"  # type: ignore[union-attr]
    await reset(runtime)


async def test_answer(
    client: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    await reset(runtime)
    offer_id = await add_offer(runtime)
    await client.put("/api/identity", json={"name": "Camille Exemple", "phone": "+41 79 000 00 00"})
    token = (await client.post("/api/extension-tokens", json={})).json()["token"]
    auth = {"Authorization": f"Bearer {token}"}
    question = {"offer_id": offer_id, "question": "Pourquoi   nous ?"}
    assert (
        await client.post("/api/extension/answer", json=question, headers=auth)
    ).status_code == 409

    calls: list[dict] = []

    class Fake:
        async def score(self, params: dict) -> RawResult:
            calls.append(params)
            return RawResult("« Parce que… »", service.MODEL, Usage(900, 0, 0, 80), "end_turn")

    monkeypatch.setattr(scoring, "make_client", lambda _settings: Fake())
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
    answered = await client.post("/api/extension/answer", json=question, headers=auth)
    assert answered.json() == {"text": "Parce que…"}
    content = calls[0]["messages"][0]["content"]
    assert "<question>\nPourquoi nous ?\n</question>" in content and "Motivé." in content
    assert "Camille" not in content and "+41" not in content  # jamais les coordonnées
    async with runtime.sessionmaker() as session:
        assert list(await session.scalars(select(LlmCall.purpose))) == ["form"]
    await reset(runtime)
