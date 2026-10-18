"""Extension du navigateur (docs/25, docs/70) : jetons, offre reconnue, données, « J'ai envoyé »,
Job-Room."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.api.routes import extension as extension_routes
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
    me = (await secured.get("/api/extension/me", headers=auth)).json()
    assert me["platform"] == "jobA1" and me["features"] == ["forms", "job-room"]
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


async def test_link_token_expires_unread(client: AsyncClient, runtime: Runtime) -> None:
    """« Relier ce navigateur » : un jeton pas lu dans les 2 minutes ne sert plus, même si la
    page qui devait le révoquer a été fermée (docs/76 §1)."""
    await reset(runtime)
    late = (await client.post("/api/extension-tokens", json={"link": True})).json()
    on_time = (await client.post("/api/extension-tokens", json={"link": True})).json()
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE extension_tokens SET expires_at = now() - interval '1 second' WHERE id = :i"
            ),
            {"i": late["id"]},
        )
    expired = {"Authorization": f"Bearer {late['token']}"}
    assert (await client.get("/api/extension/me", headers=expired)).status_code == 401
    assert [t["id"] for t in (await client.get("/api/extension-tokens")).json()] == [on_time["id"]]
    # Lu à temps : il devient un jeton ordinaire, sans délai.
    fresh = {"Authorization": f"Bearer {on_time['token']}"}
    assert (await client.get("/api/extension/me", headers=fresh)).status_code == 200
    async with runtime.engine.begin() as conn:
        left = await conn.scalar(
            text("SELECT expires_at FROM extension_tokens WHERE id = :i"), {"i": on_time["id"]}
        )
    assert left is None
    # Un jeton créé à la main n'a jamais de délai.
    manual = (await client.post("/api/extension-tokens", json={})).json()
    async with runtime.engine.begin() as conn:
        assert (
            await conn.scalar(
                text("SELECT expires_at FROM extension_tokens WHERE id = :i"), {"i": manual["id"]}
            )
        ) is None
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

    calls: list[dict[str, Any]] = []

    class Fake:
        async def score(self, params: dict[str, Any]) -> RawResult:
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


async def test_job_room_list_fill_and_declared(
    client: AsyncClient, secured: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    await reset(runtime)
    monkeypatch.setattr(extension_routes, "local_today", lambda: date(2026, 11, 3))
    for sent_at, company in (
        ("2026-11-02", "Delta SA"),
        ("2026-10-20", "Beta SA"),
        ("2026-10-02", "Alpha SA"),
        ("2026-09-28", "Ancienne SA"),  # avant le mois précédent : pas proposée
    ):
        response = await client.post(
            "/api/applications",
            json={
                "sent_at": sent_at,
                "company": company,
                "job_title": "DevOps",
                "company_address": "Rue du Test 1, 1000 Lausanne",
                "method": "electronique",
                "rate_text": "temps partiel (80 %)",
            },
        )
        assert response.status_code == 201
    token = (await client.post("/api/extension-tokens", json={})).json()["token"]
    auth = {"Authorization": f"Bearer {token}"}

    # Connexion obligatoire : sans jeton, rien.
    assert (await secured.get("/api/extension/job-room")).status_code == 401

    listed = (await client.get("/api/extension/job-room", headers=auth)).json()["items"]
    assert [i["company"] for i in listed] == ["Alpha SA", "Beta SA", "Delta SA"]
    first = listed[0]["id"]

    values = (
        await client.get(f"/api/extension/applications/{first}/job-room", headers=auth)
    ).json()
    assert values["date"] == "02.10.2026" and values["channel"] == "electronic"
    assert (values["street"], values["number"], values["postcode_city"]) == (
        "Rue du Test",
        "1",
        "1000 Lausanne",
    )
    assert (values["rate"], values["interview"], values["result"]) == (
        "PARTTIME",
        False,
        "PENDING",
    )
    missing = await client.get("/api/extension/applications/999999/job-room", headers=auth)
    assert missing.status_code == 404

    left = await client.put(f"/api/extension/applications/{first}/job-room", headers=auth)
    assert [i["company"] for i in left.json()["items"]] == ["Beta SA", "Delta SA"]
    async with runtime.sessionmaker() as session:
        declared = await session.get(Application, first)
        assert declared is not None and declared.job_room_at is not None
