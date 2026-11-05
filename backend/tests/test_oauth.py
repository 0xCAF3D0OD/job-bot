"""Se connecter avec Google, Microsoft ou Apple (docs/65, complément du 2026-11-05).

Le fournisseur est simulé : une clé RSA (et une clé EC pour Apple) signe les jetons d'identité,
ses clés publiques sont servies comme celles du fournisseur. Aucun appel réseau réel.
"""

import time
from collections.abc import AsyncIterator, Callable
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from structlog.testing import capture_logs

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.api.routes import auth as auth_routes
from jobbot.api.routes import oauth as oauth_routes
from jobbot.auth import oidc, passwords, signup
from jobbot.db.models import OauthLink, User
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings

OWNER_PASSWORD = "le-mot-de-passe-de-l-exploitant"
GUEST_PASSWORD = "un-mot-de-passe-de-test"
# Valeurs factices, reconnaissables comme telles (S-2).
GOOGLE_ID = "fictif-google.apps.example"
MICROSOFT_ID = "00000000-0000-0000-0000-00000000f1c7"
APPLE_ID = "ch.example.fictif"
TENANT = "9188040d-6c67-4c5b-b112-36a304b66dad"
EMAIL = "camille@example.ch"

RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
EC_KEY = ec.generate_private_key(ec.SECP256R1())
APPLE_P8 = EC_KEY.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()


def _jwk() -> dict[str, Any]:
    key: dict[str, Any] = jwt.algorithms.RSAAlgorithm.to_jwk(RSA_KEY.public_key(), as_dict=True)
    return key | {"kid": "fictif-1", "alg": "RS256", "use": "sig"}


def settings(**overrides: object) -> Any:
    values: dict[str, object] = {
        "auth_enabled": True,
        "public_url": "http://localhost",
        "oauth_google_client_id": GOOGLE_ID,
        "oauth_google_client_secret": "fictif-secret-google",
        "oauth_microsoft_client_id": MICROSOFT_ID,
        "oauth_microsoft_client_secret": "fictif-secret-microsoft",
        "oauth_apple_service_id": APPLE_ID,
        "oauth_apple_team_id": "FICTIF0001",
        "oauth_apple_key_id": "FICTIFKEY1",
        "oauth_apple_private_key": APPLE_P8,
    }
    values.update(overrides)
    return make_settings(**values)


class Provider:
    """Le fournisseur simulé : le prochain jeton d'identité rendu par l'échange du code."""

    def __init__(self) -> None:
        self.claims: dict[str, Any] = {}
        self.token_requests: list[dict[str, list[str]]] = []
        self.refuse = False
        self.signing_key: Any = RSA_KEY

    def handler(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(("/certs", "/keys")):
            return httpx.Response(200, json={"keys": [_jwk()]})
        self.token_requests.append(parse_qs(request.content.decode()))
        if self.refuse:
            return httpx.Response(400, json={"error": "invalid_grant"})
        token = jwt.encode(
            self.claims, self.signing_key, algorithm="RS256", headers={"kid": "fictif-1"}
        )
        return httpx.Response(200, json={"id_token": token, "access_token": "fictif-acces"})


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch) -> Provider:
    fake = Provider()
    monkeypatch.setattr(
        oauth_routes,
        "http_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(fake.handler)),
    )
    oidc.key_cache.keys.clear()
    return fake


async def clean() -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE id <> (SELECT min(id) FROM users)"))
        await conn.execute(text("TRUNCATE oauth_links, platform_settings, sessions"))
        await conn.execute(text("DELETE FROM notifications WHERE kind = 'signup_request'"))
        await conn.execute(text("UPDATE users SET password_hash = '!'"))


@pytest.fixture
async def secured() -> AsyncIterator[Runtime]:
    """Connexion activée, exploitant configuré, demandes de compte fermées (sur invitation)."""
    runtime = Runtime.create(settings())
    auth_routes.throttle.failures.clear()
    auth_routes.signup_limit.hits.clear()
    oauth_routes.start_limit.hits.clear()
    oidc.flows.items.clear()
    await clean()
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("UPDATE users SET password_hash = :h"),
            {"h": passwords.hash_password(OWNER_PASSWORD)},
        )
    yield runtime
    await clean()
    await runtime.dispose()


def client(runtime: Runtime) -> AsyncClient:
    app = create_app(runtime.settings, runtime)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


async def add_guest(runtime: Runtime, username: str = "camille") -> int:
    async with runtime.sessionmaker.begin() as session:
        user = User(username=username, password_hash=passwords.hash_password(GUEST_PASSWORD))
        session.add(user)
        await session.flush()
        return user.id


async def add_link(
    account: int, provider: str, subject: str, email: str | None = None, verified: bool = False
) -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO oauth_links (user_id, provider, subject, email, email_verified) "
                "VALUES (:u, :p, :s, :e, :v)"
            ),
            {"u": account, "p": provider, "s": subject, "e": email, "v": verified},
        )


def claims(name: str, nonce: str, **changes: Any) -> dict[str, Any]:
    now = int(time.time())
    base: dict[str, Any] = {
        "iat": now,
        "exp": now + 600,
        "nonce": nonce,
        "sub": "sujet-fictif-1",
        "email": EMAIL,
        "email_verified": True,
    }
    if name == "google":
        base |= {"iss": "https://accounts.google.com", "aud": GOOGLE_ID}
    elif name == "microsoft":
        base |= {
            "iss": f"https://login.microsoftonline.com/{TENANT}/v2.0",
            "aud": MICROSOFT_ID,
            "tid": TENANT,
        }
    else:
        base |= {"iss": "https://appleid.apple.com", "aud": APPLE_ID, "email_verified": "true"}
    return base | changes


async def sign_in(
    api: AsyncClient,
    fake: Provider,
    name: str = "google",
    *,
    query: str = "",
    edit: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    state: str | None = None,
    form: dict[str, str] | None = None,
) -> httpx.Response:
    """Un aller-retour complet : départ, consentement simulé, retour."""
    start = await api.get(f"/api/auth/oauth/{name}/start{query}")
    assert start.status_code == 303, start.text
    params = parse_qs(urlparse(start.headers["location"]).query)
    token_claims = claims(name, params["nonce"][0])
    fake.claims = edit(token_claims) if edit else token_claims
    sent_state = state if state is not None else params["state"][0]
    if name == "apple":
        return await api.post(
            f"/api/auth/oauth/{name}/callback",
            data={"code": "code-fictif", "state": sent_state, **(form or {})},
            headers={"sec-fetch-site": "cross-site", "origin": "https://appleid.apple.com"},
        )
    return await api.get(
        f"/api/auth/oauth/{name}/callback", params={"code": "code-fictif", "state": sent_state}
    )


async def links(runtime: Runtime) -> list[tuple[int, str, str | None, bool]]:
    async with admin_engine().connect() as conn:
        rows = await conn.execute(
            text("SELECT user_id, provider, email, email_verified FROM oauth_links ORDER BY id")
        )
        return [tuple(row) for row in rows]  # type: ignore[misc]


# --- Les fournisseurs proposés -----------------------------------------------------------


async def test_providers_only_when_configured(secured: Runtime) -> None:
    async with client(secured) as api:
        assert (await api.get("/api/auth/providers")).json() == {
            "providers": ["apple", "google", "microsoft"]
        }
    bare = Runtime.create(make_settings(auth_enabled=True))
    try:
        async with client(bare) as api:
            assert (await api.get("/api/auth/providers")).json() == {"providers": []}
            # Un fournisseur non configuré n'a pas de départ.
            assert (await api.get("/api/auth/oauth/google/start")).status_code == 404
    finally:
        await bare.dispose()
    half = settings(oauth_google_client_secret="", oauth_apple_private_key="")
    assert half.oauth_providers == ["microsoft"]
    assert settings(demo=True, anthropic_api_key=None).oauth_providers == []


async def test_start_sends_pkce_state_and_nonce(secured: Runtime) -> None:
    async with client(secured) as api:
        start = await api.get("/api/auth/oauth/google/start?suite=/candidatures")
    assert start.status_code == 303
    url = urlparse(start.headers["location"])
    params = parse_qs(url.query)
    assert url.netloc == "accounts.google.com"
    assert params["client_id"] == [GOOGLE_ID]
    assert params["redirect_uri"] == ["http://localhost/api/auth/oauth/google/callback"]
    assert params["code_challenge_method"] == ["S256"]
    assert len(params["state"][0]) >= 32 and len(params["nonce"][0]) >= 32
    cookie = start.headers["set-cookie"]
    assert cookie.startswith(f"{oidc.FLOW_COOKIE}=") and "HttpOnly" in cookie
    # Le parcours (state, nonce, vérificateur) reste sur le serveur, pas dans le cookie.
    assert params["state"][0] not in cookie
    flow = next(iter(oidc.flows.items.values()))
    assert flow.next_path == "/candidatures"
    assert oidc.pkce_challenge(flow.verifier) == params["code_challenge"][0]


async def test_apple_start_uses_form_post_and_signed_secret(secured: Runtime) -> None:
    async with client(secured) as api:
        start = await api.get("/api/auth/oauth/apple/start")
    params = parse_qs(urlparse(start.headers["location"]).query)
    assert params["response_mode"] == ["form_post"]
    secret = oidc.apple_client_secret(secured.settings)
    assert jwt.get_unverified_header(secret)["kid"] == "FICTIFKEY1"
    decoded = jwt.decode(
        secret, EC_KEY.public_key(), algorithms=["ES256"], audience="https://appleid.apple.com"
    )
    assert decoded["iss"] == "FICTIF0001" and decoded["sub"] == APPLE_ID
    assert decoded["exp"] - decoded["iat"] <= 300


# --- Les cas de la connexion (point 6) ----------------------------------------------------


async def test_existing_link_opens_the_session(secured: Runtime, provider: Provider) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "google", "sujet-fictif-1")
    async with client(secured) as api:
        back = await sign_in(api, provider, query="?suite=/candidatures")
        assert back.status_code == 303
        # Un compte invité qui n'a pas fini l'accueil le reprend (docs/66 §4).
        assert back.headers["location"] == "/bienvenue"
        cookies = back.headers.get_list("set-cookie")
        assert any(c.startswith("jobbot_session=") and "HttpOnly" in c for c in cookies)
        me = (await api.get("/api/auth/me")).json()
        assert me["authenticated"] and me["username"] == "camille"
    # Le code a été échangé avec le vérificateur PKCE et le secret client.
    sent = provider.token_requests[-1]
    assert sent["code_verifier"] and sent["client_secret"] == ["fictif-secret-google"]
    assert sent["grant_type"] == ["authorization_code"]


async def test_existing_link_follows_suite_when_welcome_is_done(
    secured: Runtime, provider: Provider, account: int
) -> None:
    await add_link(account, "microsoft", "sujet-fictif-1")
    async with client(secured) as api:
        back = await sign_in(api, provider, "microsoft", query="?suite=/candidatures")
    assert back.headers["location"] == "/candidatures"
    # Une adresse externe n'est pas suivie.
    async with client(secured) as api:
        back = await sign_in(api, provider, "microsoft", query="?suite=//piege.example")
    assert back.headers["location"] == "/aujourdhui"


async def test_verified_email_links_the_existing_account(
    secured: Runtime, provider: Provider
) -> None:
    guest = await add_guest(secured)
    # L'e-mail a déjà été vérifié par Apple sur ce compte.
    await add_link(guest, "apple", "sujet-apple", EMAIL, verified=True)
    async with client(secured) as api:
        back = await sign_in(api, provider, "google", edit=lambda c: c | {"email": EMAIL.upper()})
        assert back.headers["location"] == "/bienvenue"
        assert (await api.get("/api/auth/me")).json()["username"] == "camille"
    assert (guest, "google", EMAIL.upper(), True) in await links(secured)


async def test_unverified_or_microsoft_email_does_not_link(
    secured: Runtime, provider: Provider
) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "apple", "sujet-apple", EMAIL, verified=True)
    async with client(secured) as api:
        back = await sign_in(api, provider, "google", edit=lambda c: c | {"email_verified": False})
        assert back.headers["location"] == "/connexion?erreur=aucun-compte&fournisseur=google"
        # Microsoft ne garantit pas l'e-mail, même s'il le dit vérifié.
        back = await sign_in(api, provider, "microsoft")
        assert back.headers["location"] == "/connexion?erreur=aucun-compte&fournisseur=microsoft"
        assert not (await api.get("/api/auth/me")).json()["authenticated"]
    assert len(await links(secured)) == 1


async def test_email_on_an_unverified_link_does_not_count(
    secured: Runtime, provider: Provider
) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "microsoft", "sujet-ms", EMAIL, verified=False)
    async with client(secured) as api:
        back = await sign_in(api, provider, "google")
    assert back.headers["location"].startswith("/connexion?erreur=aucun-compte")


async def test_invitation_only_refuses(secured: Runtime, provider: Provider) -> None:
    async with client(secured) as api:
        back = await sign_in(api, provider)
    assert back.headers["location"] == "/connexion?erreur=aucun-compte&fournisseur=google"
    async with secured.sessionmaker() as session:
        assert list(await session.scalars(select(User.id).where(User.approved_at.is_(None)))) == []
    assert await links(secured) == []


async def test_open_signup_creates_a_pending_request(
    secured: Runtime, provider: Provider, account: int
) -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("INSERT INTO platform_settings (key, value) VALUES (:k, 'true'::jsonb)"),
            {"k": signup.OPEN_KEY},
        )
    async with client(secured) as api:
        back = await sign_in(api, provider)
        assert back.headers["location"] == "/connexion?info=demande&fournisseur=google"
        assert not (await api.get("/api/auth/me")).json()["authenticated"]
        # Tant que l'exploitant n'a pas accepté : « en attente », sans session.
        again = await sign_in(api, provider)
        assert again.headers["location"] == "/connexion?erreur=en-attente&fournisseur=google"
    async with secured.sessionmaker() as session:
        user = await session.scalar(select(User).where(User.approved_at.is_(None)))
    assert user is not None and user.username == "camille"
    assert user.password_hash == accounts.UNUSABLE_PASSWORD
    assert (user.id, "google", EMAIL, True) in await links(secured)
    # Accepté : la connexion passe.
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("UPDATE users SET approved_at = now() WHERE id = :i"), {"i": user.id}
        )
    async with client(secured) as api:
        back = await sign_in(api, provider)
        assert back.headers["location"] == "/bienvenue"
    # Le mot de passe vide ne permet pas de se connecter avec l'identifiant.
    async with client(secured) as api:
        refused = await api.post("/api/auth/login", json={"username": "camille", "password": "!"})
        assert refused.status_code == 401


async def test_suspended_account_is_refused(secured: Runtime, provider: Provider) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "google", "sujet-fictif-1")
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("UPDATE users SET suspended_at = now() WHERE id = :i"), {"i": guest}
        )
    async with client(secured) as api:
        back = await sign_in(api, provider)
    assert back.headers["location"] == "/connexion?erreur=suspendu&fournisseur=google"


# --- state, nonce et jeton d'identité ------------------------------------------------------


async def test_wrong_state_is_refused(secured: Runtime, provider: Provider) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "google", "sujet-fictif-1")
    async with client(secured) as api:
        back = await sign_in(api, provider, state="un-autre-state")
        assert back.headers["location"] == "/connexion?erreur=refuse&fournisseur=google"
        assert not (await api.get("/api/auth/me")).json()["authenticated"]
    # Le code n'a même pas été échangé.
    assert provider.token_requests == []


async def test_flow_serves_once_and_needs_its_cookie(secured: Runtime, provider: Provider) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "google", "sujet-fictif-1")
    async with client(secured) as api:
        start = await api.get("/api/auth/oauth/google/start")
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        nonce = parse_qs(urlparse(start.headers["location"]).query)["nonce"][0]
        provider.claims = claims("google", nonce)
        # Sans le cookie du parcours (autre navigateur) : refusé, même avec le bon state.
        api.cookies.clear()
        stolen = await api.get(
            "/api/auth/oauth/google/callback", params={"code": "c", "state": state}
        )
        assert stolen.headers["location"] == "/connexion?erreur=expire&fournisseur=google"
    async with client(secured) as api:
        good = await sign_in(api, provider)
        assert good.headers["location"] == "/bienvenue"
        # Le parcours réussi est consommé ; reste celui abandonné plus haut.
        assert len(oidc.flows.items) == 1


async def test_wrong_nonce_is_refused(secured: Runtime, provider: Provider) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "google", "sujet-fictif-1")
    async with client(secured) as api:
        back = await sign_in(api, provider, edit=lambda c: c | {"nonce": "rejoue"})
        assert back.headers["location"] == "/connexion?erreur=refuse&fournisseur=google"
        assert not (await api.get("/api/auth/me")).json()["authenticated"]


@pytest.mark.parametrize(
    "change",
    [
        {"exp": int(time.time()) - 3600, "iat": int(time.time()) - 7200},
        {"aud": "une-autre-app"},
        {"iss": "https://piege.example"},
    ],
    ids=["expire", "audience", "emetteur"],
)
async def test_bad_id_token_is_refused(
    secured: Runtime, provider: Provider, change: dict[str, Any]
) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "google", "sujet-fictif-1")
    async with client(secured) as api:
        back = await sign_in(api, provider, edit=lambda c: c | change)
        assert back.headers["location"] == "/connexion?erreur=refuse&fournisseur=google"
        assert not (await api.get("/api/auth/me")).json()["authenticated"]


async def test_microsoft_issuer_must_match_the_tenant(secured: Runtime, provider: Provider) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "microsoft", "sujet-fictif-1")
    other = "11111111-1111-1111-1111-111111111111"
    async with client(secured) as api:
        back = await sign_in(api, provider, "microsoft", edit=lambda c: c | {"tid": other})
        assert back.headers["location"] == "/connexion?erreur=refuse&fournisseur=microsoft"


async def test_signature_from_another_key_is_refused(secured: Runtime, provider: Provider) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "google", "sujet-fictif-1")
    # Signé par une autre clé, sous le même `kid` que la clé publiée.
    provider.signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    async with client(secured) as api:
        back = await sign_in(api, provider)
    assert back.headers["location"] == "/connexion?erreur=refuse&fournisseur=google"


async def test_cancel_and_provider_error(secured: Runtime, provider: Provider) -> None:
    async with client(secured) as api:
        start = await api.get("/api/auth/oauth/google/start")
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        back = await api.get(
            "/api/auth/oauth/google/callback", params={"error": "access_denied", "state": state}
        )
        assert back.headers["location"] == "/connexion?erreur=annule&fournisseur=google"
        provider.refuse = True
        back = await sign_in(api, provider)
        assert back.headers["location"] == "/connexion?erreur=refuse&fournisseur=google"


# --- Apple -------------------------------------------------------------------------------


async def test_apple_form_post_stores_the_first_email(secured: Runtime, provider: Provider) -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("INSERT INTO platform_settings (key, value) VALUES (:k, 'true'::jsonb)"),
            {"k": signup.OPEN_KEY},
        )
    relay = "fictif01@privaterelay.appleid.com"
    first = '{"name":{"firstName":"Camille"},"email":"' + relay + '"}'
    async with client(secured) as api:
        # Venue du site d'Apple (POST d'un autre site) : acceptée, le state fait foi.
        back = await sign_in(
            api,
            provider,
            "apple",
            edit=lambda c: {k: v for k, v in c.items() if k != "email"},
            form={"user": first},
        )
        assert back.status_code == 303
        assert back.headers["location"] == "/connexion?info=demande&fournisseur=apple"
    stored = await links(secured)
    assert stored[0][1:] == ("apple", relay, False)
    # Les fois suivantes, Apple n'envoie plus ni `user` ni toujours l'e-mail : le lien reste.
    async with admin_engine().begin() as conn:
        await conn.execute(text("UPDATE users SET approved_at = now() WHERE approved_at IS NULL"))
    async with client(secured) as api:
        back = await sign_in(
            api, provider, "apple", edit=lambda c: {k: v for k, v in c.items() if k != "email"}
        )
        assert back.headers["location"] == "/bienvenue"
    assert (await links(secured))[0][2] == relay


async def test_cross_site_post_elsewhere_still_refused(secured: Runtime) -> None:
    async with client(secured) as api:
        refused = await api.post(
            "/api/auth/oauth/google/callback",
            data={"code": "c", "state": "s"},
            headers={"sec-fetch-site": "cross-site"},
        )
    assert refused.status_code == 403


# --- Compte, Connexions (point 7) ---------------------------------------------------------


async def login(api: AsyncClient, username: str = "camille") -> None:
    response = await api.post(
        "/api/auth/login", json={"username": username, "password": GUEST_PASSWORD}
    )
    assert response.status_code == 204


async def test_link_from_connections_then_remove(secured: Runtime, provider: Provider) -> None:
    guest = await add_guest(secured)
    async with client(secured) as api:
        # Sans session, « lier » renvoie à la connexion.
        anonymous = await api.get("/api/auth/oauth/google/start?lier=1")
        assert anonymous.headers["location"].startswith("/connexion")
        await login(api)
        back = await sign_in(api, provider, query="?lier=1")
        assert back.headers["location"] == "/reglages?rubrique=connexions&lie=google"
        listed = (await api.get("/api/account/connexions")).json()
        assert listed["providers"] == ["apple", "google", "microsoft"]
        assert listed["has_password"] is True
        assert [(x["provider"], x["email"]) for x in listed["links"]] == [("google", EMAIL)]
        link_id = listed["links"][0]["id"]
        # Le mot de passe reste : le lien peut partir.
        assert (await api.delete(f"/api/account/connexions/{link_id}")).status_code == 204
        assert (await api.get("/api/account/connexions")).json()["links"] == []
    assert await links(secured) == []
    assert guest


async def test_last_way_to_sign_in_cannot_be_removed(secured: Runtime, provider: Provider) -> None:
    async with secured.sessionmaker.begin() as session:
        user = User(username="sans-mot", password_hash=accounts.UNUSABLE_PASSWORD)
        session.add(user)
        await session.flush()
        account = user.id
    await add_link(account, "google", "sujet-fictif-1")
    async with client(secured) as api:
        assert (await sign_in(api, provider)).headers["location"] == "/bienvenue"
        listed = (await api.get("/api/account/connexions")).json()
        assert listed["has_password"] is False
        only = listed["links"][0]["id"]
        refused = await api.delete(f"/api/account/connexions/{only}")
        assert refused.status_code == 409
        # Avec un second lien, le premier peut partir.
        back = await sign_in(api, provider, "microsoft", query="?lier=1")
        assert back.headers["location"] == "/reglages?rubrique=connexions&lie=microsoft"
        assert (await api.delete(f"/api/account/connexions/{only}")).status_code == 204


async def test_link_owned_elsewhere_and_second_account(
    secured: Runtime, provider: Provider
) -> None:
    guest = await add_guest(secured)
    other = await add_guest(secured, "dominique")
    await add_link(other, "google", "sujet-fictif-1")
    async with admin_engine().connect() as conn:
        other_link = (await conn.execute(text("SELECT id FROM oauth_links"))).scalar_one()
    async with client(secured) as api:
        await login(api)
        back = await sign_in(api, provider, query="?lier=1")
        assert back.headers["location"] == (
            "/reglages?rubrique=connexions&erreur=deja-lie&fournisseur=google"
        )
        # Le lien d'un autre compte n'existe pas pour celui-ci (C-4) ; il ne se voit pas non plus.
        assert (await api.delete(f"/api/account/connexions/{other_link}")).status_code == 404
        assert (await api.get("/api/account/connexions")).json()["links"] == []
    with accounts.use(guest):
        async with secured.sessionmaker() as session:
            assert list(await session.scalars(select(OauthLink))) == []
    assert (other, "google", None, False) in await links(secured)


async def test_connections_need_a_session(secured: Runtime) -> None:
    async with client(secured) as api:
        assert (await api.get("/api/account/connexions")).status_code == 401
        assert (await api.delete("/api/account/connexions/1")).status_code == 401


# --- Le journal (point 8) ----------------------------------------------------------------


async def test_journal_without_token_or_email(secured: Runtime, provider: Provider) -> None:
    guest = await add_guest(secured)
    await add_link(guest, "google", "sujet-fictif-1")
    with capture_logs() as logs:
        async with client(secured) as api:
            await sign_in(api, provider)
            await sign_in(api, provider, "microsoft")
    events = {entry["event"]: entry for entry in logs}
    assert events["oauth_login_succeeded"]["provider"] == "google"
    assert events["oauth_login_succeeded"]["account"] == guest
    assert events["oauth_login_refused"]["provider"] == "microsoft"
    assert events["oauth_login_refused"]["reason"] == "aucun-compte"
    written = repr(logs)
    for secret in (EMAIL, "sujet-fictif-1", "code-fictif", "fictif-acces", "fictif-secret"):
        assert secret not in written
