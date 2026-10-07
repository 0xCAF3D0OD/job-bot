"""Connexion (docs/18 §1) : comptes, sessions, routes réservées, essais limités, CSRF."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text, update

from jobbot import __main__ as cli
from jobbot.api.app import create_app
from jobbot.api.routes import auth as auth_routes
from jobbot.auth import passwords, service
from jobbot.auth.middleware import cross_site, is_public, secure_cookie
from jobbot.db.models import User, UserSession
from jobbot.runtime import Runtime

from .conftest import make_settings

PASSWORD = "un-mot-de-passe-de-test"


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(auth_enabled=True))
    auth_routes.throttle.failures.clear()
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE users CASCADE"))
    yield runtime
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE users CASCADE"))
    await runtime.dispose()


async def add_user(rt: Runtime, username: str = "camille") -> None:
    async with rt.sessionmaker.begin() as session:
        session.add(User(username=username, password_hash=passwords.hash_password(PASSWORD)))


def client(rt: Runtime) -> AsyncClient:
    app = create_app(rt.settings, rt)
    # « localhost » : cookie sans l'attribut Secure, renvoyé en HTTP par le client de test.
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


def test_passwords() -> None:
    stored = passwords.hash_password(PASSWORD)
    assert stored.startswith("scrypt$") and PASSWORD not in stored
    assert passwords.verify_password(PASSWORD, stored)
    assert not passwords.verify_password("autre chose", stored)
    assert not passwords.verify_password(PASSWORD, "n'importe quoi")
    assert passwords.hash_password(PASSWORD) != stored  # sel aléatoire
    assert passwords.check_strength("court") and passwords.check_strength(" espace-au-debut")
    assert passwords.check_strength(PASSWORD) is None


def test_rules() -> None:
    assert is_public("GET", "/api/news") and is_public("GET", "/api/news/items/3/image")
    assert not is_public("POST", "/api/news/seen") and not is_public("GET", "/api/offers")
    assert not is_public("PUT", "/api/news/preferences") and is_public("POST", "/api/auth/login")
    assert cross_site("POST", {"sec-fetch-site": "cross-site"})
    assert not cross_site("POST", {"sec-fetch-site": "same-origin"})
    assert not cross_site("GET", {"sec-fetch-site": "cross-site"})
    assert cross_site("POST", {"origin": "https://piege.example", "host": "jobbot.example"})
    assert not cross_site("POST", {"origin": "https://jobbot.example", "host": "jobbot.example"})
    assert not cross_site("POST", {})
    assert not secure_cookie({"host": "localhost:5173"})
    assert secure_cookie({"host": "abc.devtunnels.ms"})


async def test_pages_reserved_until_login(rt: Runtime) -> None:
    async with client(rt) as api:
        me = (await api.get("/api/auth/me")).json()
        assert me == {
            "authenticated": False,
            "username": None,
            "setup_needed": True,
            "auth_enabled": True,
        }
        assert (
            await api.post("/api/auth/login", json={"username": "x", "password": "y"})
        ).status_code == 409
        await add_user(rt)
        assert (await api.get("/api/auth/me")).json()["setup_needed"] is False
        # Réservé : offres, candidatures, ORP, formations, profils, réglages, modifications.
        for path in (
            "/api/offers",
            "/api/applications",
            "/api/orp",
            "/api/trainings",
            "/api/profiles",
            "/api/settings",
            "/api/inbox",
        ):
            assert (await api.get(path)).status_code == 401, path
        assert (await api.post("/api/news/seen")).status_code == 401
        # Ouvert : les Actualités en lecture (profil principal, même si un autre est demandé).
        assert (await api.get("/api/news", headers={"X-Jobbot-Profile": "999"})).status_code == 200
        assert (await api.get("/api/news/preferences")).status_code == 200

        bad = await api.post("/api/auth/login", json={"username": "camille", "password": "faux"})
        assert bad.status_code == 401
        good = await api.post(
            "/api/auth/login", json={"username": " Camille ", "password": PASSWORD}
        )
        assert good.status_code == 204
        cookie = good.headers["set-cookie"]
        assert "HttpOnly" in cookie and "SameSite=Lax" in cookie and "Max-Age=2592000" in cookie
        assert "Secure" not in cookie  # localhost
        assert (await api.get("/api/auth/me")).json()["username"] == "camille"
        assert (await api.get("/api/orp")).status_code == 200

        assert (await api.post("/api/auth/logout")).status_code == 204
        assert (await api.get("/api/orp")).status_code == 401
    async with rt.sessionmaker() as session:
        assert list(await session.scalars(select(UserSession))) == []


async def test_sessions_expire_renew_and_close(rt: Runtime) -> None:
    await add_user(rt)
    async with client(rt) as api, client(rt) as other:
        for c in (api, other):
            await c.post("/api/auth/login", json={"username": "camille", "password": PASSWORD})
        # Session vieille de deux jours : prolongée, cookie renvoyé.
        async with rt.sessionmaker.begin() as session:
            await session.execute(
                update(UserSession).values(last_seen_at=datetime.now(UTC) - timedelta(days=2))
            )
        renewed = await api.get("/api/orp")
        assert renewed.status_code == 200 and "set-cookie" in renewed.headers
        assert "set-cookie" not in (await api.get("/api/orp")).headers
        # « Se déconnecter partout » ferme aussi l'autre navigateur.
        assert (await api.post("/api/auth/logout-all")).status_code == 204
        assert (await other.get("/api/orp")).status_code == 401
        assert (await api.post("/api/auth/logout-all")).status_code == 401
        # Session expirée : refusée et effacée.
        await other.post("/api/auth/login", json={"username": "camille", "password": PASSWORD})
        async with rt.sessionmaker.begin() as session:
            await session.execute(update(UserSession).values(expires_at=datetime.now(UTC)))
        assert (await other.get("/api/orp")).status_code == 401
    async with rt.sessionmaker() as session:
        assert list(await session.scalars(select(UserSession))) == []


async def test_attempts_are_throttled(rt: Runtime) -> None:
    await add_user(rt)
    async with client(rt) as api:
        for _ in range(service.FREE_ATTEMPTS):
            r = await api.post("/api/auth/login", json={"username": "camille", "password": "faux"})
            assert r.status_code == 401
        blocked = await api.post(
            "/api/auth/login", json={"username": "camille", "password": PASSWORD}
        )
        assert blocked.status_code == 429 and int(blocked.headers["retry-after"]) >= 1


async def test_cross_site_changes_refused(rt: Runtime) -> None:
    await add_user(rt)
    async with client(rt) as api:
        await api.post("/api/auth/login", json={"username": "camille", "password": PASSWORD})
        refused = await api.post("/api/news/seen", headers={"Sec-Fetch-Site": "cross-site"})
        assert refused.status_code == 403
        assert (
            await api.post("/api/news/seen", headers={"Sec-Fetch-Site": "same-origin"})
        ).status_code == 204


async def test_auth_disabled_opens_everything(runtime: Runtime) -> None:
    app = create_app(runtime.settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        assert (await api.get("/api/orp")).status_code == 200
        assert (await api.get("/api/auth/me")).json()["auth_enabled"] is False


def test_set_password_command(
    rt: Runtime, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = iter([PASSWORD, PASSWORD])
    monkeypatch.setattr(cli, "_settings", lambda: rt.settings)
    monkeypatch.setattr("builtins.input", lambda _prompt: "camille")
    monkeypatch.setattr("getpass.getpass", lambda _prompt: next(answers))
    assert cli.main(["set-password"]) == 0
    output = capsys.readouterr().out
    assert "Compte créé pour « camille »" in output and PASSWORD not in output

    monkeypatch.setattr("getpass.getpass", lambda _prompt: "court")
    assert cli.main(["set-password"]) == 1
    assert "au moins 12 caractères" in capsys.readouterr().err
