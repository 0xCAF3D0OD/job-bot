"""« Se connecter avec jobA1 » depuis Get'emAll (docs/140) : autorisation, échange, lecture.

Les cas du plan (docs/140 §6) : code brûlé après une lecture, expiré après 60 s, PKCE faux refusé,
adresse de retour hors liste refusée, second compte en 404 (C-4), champs ORP absents sans la
case, aucune coordonnée rendue, export et suppression.
"""

import base64
import hashlib
import io
import json
import secrets
import zipfile
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urlsplit

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import text

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.api.routes import partners as partner_routes
from jobbot.auth import passwords
from jobbot.db.models import Application, Contact, Offer, Setting, User
from jobbot.partners import getemall as service
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings

SECRET = "secret-client-de-test-" + "x" * 20
REDIRECT = "https://getthemall.ch/connexion"
OTHER = "compte-getemall-b"
BASE = "/api/partenaires/getemall"


def pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


async def clean() -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("TRUNCATE partner_codes, partner_links, applications, offers, contacts CASCADE")
        )
        await conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": OTHER})
        await conn.execute(text("UPDATE users SET getemall_tester = false"))
        await conn.execute(
            text("DELETE FROM settings WHERE key LIKE 'identity_%' OR key LIKE 'orp_%'")
        )
        await conn.execute(text("DELETE FROM notifications"))


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    await clean()
    partner_routes.throttle.failures.clear()
    runtime = Runtime.create(
        make_settings(getemall_client_secret=SECRET, getemall_redirect_uris=[REDIRECT])
    )
    async with admin_engine().begin() as conn:
        await conn.execute(text("UPDATE users SET getemall_tester = true"))
    yield runtime
    await runtime.dispose()
    await clean()


@pytest.fixture
async def api(rt: Runtime) -> AsyncIterator[AsyncClient]:
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def authorize(api: AsyncClient, *, orp: bool = False) -> tuple[str, str]:
    """« Autoriser » : le code rendu dans l'adresse de retour, et son vérificateur."""
    verifier, challenge = pkce()
    response = await api.post(
        f"{BASE}/autorisation",
        json={
            "redirect_uri": REDIRECT,
            "state": "etat-de-test-123",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "orp": orp,
        },
    )
    assert response.status_code == 200, response.text
    target = urlsplit(response.json()["redirect_to"])
    assert f"{target.scheme}://{target.netloc}{target.path}" == REDIRECT
    query = parse_qs(target.query)
    assert query["state"] == ["etat-de-test-123"]
    return query["code"][0], verifier


async def exchange(
    api: AsyncClient, code: str, verifier: str, *, redirect: str = REDIRECT, secret: str = SECRET
) -> Response:
    return await api.post(
        f"{BASE}/echange",
        json={
            "client_secret": secret,
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": redirect,
        },
    )


async def link(api: AsyncClient, *, orp: bool = False) -> dict[str, object]:
    code, verifier = await authorize(api, orp=orp)
    response = await exchange(api, code, verifier)
    assert response.status_code == 200, response.text
    granted: dict[str, object] = response.json()
    return granted


async def link_as(api: AsyncClient, rt: Runtime, user_id: int) -> dict[str, object]:
    """Une liaison pour un autre compte : l'API d'essai, sans connexion, agit au nom de
    l'exploitant ; le code est donc tiré directement au nom de ce compte."""
    verifier, challenge = pkce()
    with accounts.use(user_id):
        async with rt.sessionmaker.begin() as session:
            code = await service.create_code(
                session, redirect_uri=REDIRECT, code_challenge=challenge, orp=False
            )
    response = await exchange(api, code, verifier)
    assert response.status_code == 200, response.text
    granted: dict[str, object] = response.json()
    return granted


def bearer(token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def add_application(rt: Runtime, **values: object) -> int:
    now = datetime.now(UTC)
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"gea-{secrets.token_hex(4)}",
            status="applied",
            first_seen_at=now,
            last_seen_at=now,
            title="Ingénieure DevOps",
            company="Exemple SA",
            description=(
                "Nous cherchons une ingénieure DevOps. Contact : Marie Recruteuse, "
                "marie@exemple.ch, 021 345 67 89. Postuler sur https://exemple.ch/jobs/1."
            ),
        )
        session.add(offer)
        await session.flush()
        application = Application(
            offer_id=offer.id,
            sent_at=date(2026, 11, 2),
            method="electronique",
            company="Exemple SA",
            job_title="Ingénieure DevOps",
            contact_name="Paul Chefdequipe",
            contact_email="paul@exemple.ch",
            status="entretien",
            interview_at=datetime(2026, 11, 12, 9, 0, tzinfo=UTC),
            orp_month=values.pop("orp_month", "2026-11"),
            **values,
        )
        session.add(application)
        await session.flush()
        session.add(
            Contact(
                offer_id=offer.id,
                name="Marie Recruteuse",
                role="recruiter",
                channel="email",
                contacted_on=date(2026, 11, 3),
            )
        )
        return application.id


async def test_full_flow_reads_the_follow_up(api: AsyncClient, rt: Runtime, account: int) -> None:
    await add_application(rt)
    granted = await link(api)
    assert str(granted["token"]).startswith("jbg_") and granted["orp"] is False
    # Un identifiant propre à Get'emAll, jamais l'id du compte.
    assert granted["subject"] != str(account) and len(str(granted["subject"])) >= 24
    response = await api.get(f"{BASE}/suivi", headers=bearer(granted["token"]))
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    # Sans la case ORP, le champ n'existe pas du tout.
    assert "orp" not in body
    profile = body["profile"]
    assert set(profile) == {"faits", "total", "prochaine"} and profile["total"] == 5
    assert 0 <= profile["faits"] <= 5 and (profile["prochaine"] is None) == (profile["faits"] == 5)
    [application] = body["applications"]
    assert application["job_title"] == "Ingénieure DevOps"
    assert application["status"] == "entretien" and application["interview_at"]
    assert set(application) == {"id", "job_title", "company", "status", "interview_at"}
    raw = response.text
    assert "Paul" not in raw and "@" not in raw
    state = (await api.get(BASE)).json()
    assert state["linked"] and state["tester"] and state["available"]
    assert state["last_used_at"] is not None


async def test_code_is_burned_after_one_reading(api: AsyncClient) -> None:
    code, verifier = await authorize(api)
    assert (await exchange(api, code, verifier)).status_code == 200
    again = await exchange(api, code, verifier)
    assert again.status_code == 400


async def test_code_expires_after_60_seconds(api: AsyncClient) -> None:
    code, verifier = await authorize(api)
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("UPDATE partner_codes SET expires_at = now() - interval '1 second'")
        )
    assert (await exchange(api, code, verifier)).status_code == 400


async def test_wrong_pkce_is_refused_and_burns_the_code(api: AsyncClient) -> None:
    code, verifier = await authorize(api)
    wrong, _ = pkce()
    assert (await exchange(api, code, wrong)).status_code == 400
    # Un seul essai par code : le bon vérificateur ne passe plus.
    assert (await exchange(api, code, verifier)).status_code == 400


async def test_unknown_redirect_is_refused(api: AsyncClient) -> None:
    _, challenge = pkce()
    response = await api.post(
        f"{BASE}/autorisation",
        json={
            "redirect_uri": "https://getthemall.ch.attaquant.example/connexion",
            "state": "etat-de-test-123",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )
    assert response.status_code == 400
    # Au moment de l'échange aussi, l'adresse doit être celle du code.
    code, verifier = await authorize(api)
    other = await exchange(api, code, verifier, redirect="https://getthemall.ch/autre")
    assert other.status_code == 400


async def test_plain_pkce_is_refused(api: AsyncClient) -> None:
    verifier, _ = pkce()
    response = await api.post(
        f"{BASE}/autorisation",
        json={
            "redirect_uri": REDIRECT,
            "state": "etat-de-test-123",
            "code_challenge": verifier[:43],
            "code_challenge_method": "plain",
        },
    )
    assert response.status_code == 422


async def test_wrong_client_secret_is_refused_then_slowed(api: AsyncClient) -> None:
    code, verifier = await authorize(api)
    for _ in range(5):
        wrong = await exchange(api, code, verifier, secret="pas-le-bon")
        assert wrong.status_code == 401
    slowed = await exchange(api, code, verifier, secret="pas-le-bon")
    assert slowed.status_code == 429
    # Un mauvais secret ne brûle pas le code (il n'a pas été lu).
    partner_routes.throttle.failures.clear()
    assert (await exchange(api, code, verifier)).status_code == 200


async def test_only_testers(api: AsyncClient, rt: Runtime) -> None:
    granted = await link(api)
    async with admin_engine().begin() as conn:
        await conn.execute(text("UPDATE users SET getemall_tester = false"))
    # Plus testeur : le jeton ne passe plus, et aucune nouvelle autorisation.
    assert (await api.get(f"{BASE}/suivi", headers=bearer(granted["token"]))).status_code == 401
    _, challenge = pkce()
    refused = await api.post(
        f"{BASE}/autorisation",
        json={
            "redirect_uri": REDIRECT,
            "state": "etat-de-test-123",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )
    assert refused.status_code == 403


async def test_orp_counts_only_with_the_box(api: AsyncClient, rt: Runtime) -> None:
    await add_application(rt)
    async with rt.sessionmaker.begin() as session:
        session.add(Setting(key="orp_monthly_target", value=10))
    granted = await link(api, orp=True)
    assert granted["orp"] is True
    body = (await api.get(f"{BASE}/suivi", headers=bearer(granted["token"]))).json()
    assert body["orp"]["target"] == 10
    assert set(body["orp"]) == {"month", "done", "target", "due_on"}
    # Une nouvelle autorisation sans la case retire les compteurs.
    granted = await link(api, orp=False)
    body = (await api.get(f"{BASE}/suivi", headers=bearer(granted["token"]))).json()
    assert "orp" not in body


async def test_offer_text_has_no_contact_details(api: AsyncClient, rt: Runtime) -> None:
    application_id = await add_application(rt)
    granted = await link(api)
    response = await api.get(
        f"{BASE}/candidatures/{application_id}/offre", headers=bearer(granted["token"])
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "Ingénieure DevOps" and body["company"] == "Exemple SA"
    text_ = body["description"]
    assert "ingénieure DevOps" in text_
    for leaked in ("Marie", "Recruteuse", "marie@exemple.ch", "021 345", "https://", "Paul"):
        assert leaked not in response.text, leaked


async def test_other_account_gets_404(api: AsyncClient, rt: Runtime, account: int) -> None:
    mine = await add_application(rt)
    async with rt.sessionmaker.begin() as session:
        other = User(
            username=OTHER,
            password_hash=passwords.hash_password("x" * 12),
            getemall_tester=True,
        )
        session.add(other)
        await session.flush()
        other_id = other.id
    granted = await link_as(api, rt, other_id)
    response = await api.get(f"{BASE}/candidatures/{mine}/offre", headers=bearer(granted["token"]))
    assert response.status_code == 404
    body = (await api.get(f"{BASE}/suivi", headers=bearer(granted["token"]))).json()
    assert body["applications"] == []


async def test_revoke_and_link_again_keeps_the_subject(api: AsyncClient) -> None:
    first = await link(api)
    assert (await api.delete(BASE)).status_code == 204
    assert (await api.get(f"{BASE}/suivi", headers=bearer(first["token"]))).status_code == 401
    assert (await api.get(BASE)).json()["linked"] is False
    second = await link(api)
    assert second["subject"] == first["subject"] and second["token"] != first["token"]
    assert (await api.get(f"{BASE}/suivi", headers=bearer(second["token"]))).status_code == 200
    # Le jeton d'avant reste refusé.
    assert (await api.get(f"{BASE}/suivi", headers=bearer(first["token"]))).status_code == 401


async def test_partner_deletes_the_link(api: AsyncClient) -> None:
    granted = await link(api)
    gone = await api.delete(f"{BASE}/lien", headers=bearer(granted["token"]))
    assert gone.status_code == 204
    assert (await api.get(f"{BASE}/suivi", headers=bearer(granted["token"]))).status_code == 401


async def test_without_token_nothing(api: AsyncClient) -> None:
    for path in ("/suivi", "/candidatures/1/offre"):
        assert (await api.get(f"{BASE}{path}")).status_code == 401
        other = await api.get(f"{BASE}{path}", headers=bearer("jbx_un-jeton-d-extension"))
        assert other.status_code == 401


async def test_not_configured(client: AsyncClient) -> None:
    """Sans secret ni adresse de retour, rien n'est proposé."""
    assert (await client.get(f"{BASE}/suivi", headers=bearer("jbg_x"))).status_code == 401
    response = await client.post(
        f"{BASE}/echange",
        json={"client_secret": "", "code": "jbc_x", "code_verifier": "x" * 43, "redirect_uri": ""},
    )
    assert response.status_code == 404
    assert (await client.get(BASE)).json()["available"] is False


async def test_export_and_deletion(api: AsyncClient, rt: Runtime, account: int) -> None:
    granted = await link(api)
    exported = await api.post("/api/account/export", json={"password": "inutile"})
    assert exported.status_code == 200, exported.text
    archive = zipfile.ZipFile(io.BytesIO(exported.content))
    links = json.loads(archive.read("data/partner_links.json"))
    assert [row["subject"] for row in links] == [granted["subject"]]
    assert "token_hash" not in links[0]
    assert "data/partner_codes.json" in archive.namelist()
    everything = b"".join(archive.read(n) for n in archive.namelist())
    assert str(granted["token"]).encode() not in everything
    # Supprimer le compte efface la liaison et les codes (clé étrangère en cascade).
    async with rt.sessionmaker.begin() as session:
        other = User(
            username=OTHER, password_hash=passwords.hash_password("x" * 12), getemall_tester=True
        )
        session.add(other)
        await session.flush()
        other_id = other.id
    await link_as(api, rt, other_id)
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": other_id})
        left = await conn.scalar(
            text(
                "select (select count(*) from partner_links where user_id = :id) "
                "+ (select count(*) from partner_codes where user_id = :id)"
            ),
            {"id": other_id},
        )
    assert left == 0


async def test_orp_switch_applies_at_once(api: AsyncClient, rt: Runtime) -> None:
    """« Partager mes recherches ORP » dans les Réglages : sans nouvelle autorisation."""
    # Sans application reliée, rien à changer.
    assert (await api.patch(BASE, json={"orp": True})).status_code == 404
    await add_application(rt)
    granted = await link(api)
    suivi = f"{BASE}/suivi"
    assert "orp" not in (await api.get(suivi, headers=bearer(granted["token"]))).json()
    shared = await api.patch(BASE, json={"orp": True})
    assert shared.status_code == 200 and shared.json()["orp"] is True
    assert "orp" in (await api.get(suivi, headers=bearer(granted["token"]))).json()
    assert (await api.patch(BASE, json={"orp": False})).json()["orp"] is False
    assert "orp" not in (await api.get(suivi, headers=bearer(granted["token"]))).json()
    # Après « Retirer », plus d'interrupteur.
    assert (await api.delete(BASE)).status_code == 204
    assert (await api.patch(BASE, json={"orp": True})).status_code == 404
