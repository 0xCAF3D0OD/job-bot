"""S'inscrire, sur demande (docs/102) : la demande et ses garde-fous, la connexion refusée
tant que le compte attend, accepter et refuser, l'effacement après 30 jours, aucune tâche."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from structlog.testing import capture_logs

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.api.routes import auth as auth_routes
from jobbot.auth import passwords, service, signup
from jobbot.db.models import Notification, User, UserSession
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings

PASSWORD = "un-mot-de-passe-solide"
OWNER_PASSWORD = "le-mot-de-passe-de-l-exploitant"


async def clean() -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE id <> (SELECT min(id) FROM users)"))
        await conn.execute(text("TRUNCATE account_links, platform_settings, sessions"))
        await conn.execute(text("DELETE FROM notifications WHERE kind = 'signup_request'"))
        await conn.execute(text("UPDATE users SET password_hash = '!'"))


@pytest.fixture
async def secured() -> AsyncIterator[Runtime]:
    """Connexion activée, exploitant configuré (avec mot de passe) : demandes ouvertes."""
    runtime = Runtime.create(make_settings(auth_enabled=True))
    auth_routes.throttle.failures.clear()
    auth_routes.signup_limit.hits.clear()
    await clean()
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("UPDATE users SET password_hash = :h"),
            {"h": passwords.hash_password(OWNER_PASSWORD)},
        )
    yield runtime
    await clean()
    auth_routes.signup_limit.hits.clear()
    await runtime.dispose()


def client(runtime: Runtime) -> AsyncClient:
    app = create_app(runtime.settings, runtime)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


def demand(username: str = "camille", **changes: Any) -> dict[str, Any]:
    return {"username": username, "password": PASSWORD, "consent": True} | changes


async def pending_ids(runtime: Runtime) -> list[int]:
    async with runtime.sessionmaker() as session:
        rows = await session.scalars(select(User.id).where(User.approved_at.is_(None)))
        return list(rows)


async def test_request_waits_for_the_owner(runtime: Runtime, secured: Runtime) -> None:
    async with client(runtime) as owner, client(secured) as guest:
        assert (await guest.get("/api/auth/signup")).json() == {"open": True}
        with capture_logs() as logs:
            sent = await guest.post(
                "/api/auth/signup", json=demand(note="Infirmière, connue par Léa")
            )
        assert sent.status_code == 204, sent.text
        # Les journaux : l'identifiant et l'adresse, jamais le mot de passe ni le mot laissé.
        assert any(
            e["event"] == "signup_requested" and e["username"] == "camille" and e["ip"]
            for e in logs
        )
        assert PASSWORD not in str(logs) and "Léa" not in str(logs)

        # L'exploitant voit la demande à part, et une alerte dans sa cloche.
        listed = (await owner.get("/api/platform")).json()
        assert "camille" not in [a["username"] for a in listed["accounts"]]
        [request] = listed["signup_requests"]
        assert request["username"] == "camille" and request["note"] == "Infirmière, connue par Léa"
        assert listed["signup_open"] is True
        async with runtime.sessionmaker() as session:
            titles = await session.scalars(
                select(Notification.title).where(Notification.kind == "signup_request")
            )
            assert list(titles) == ["Nouvelle demande de compte : camille"]

        # Rien ne tourne pour lui, et il n'a rien : ni profil, ni adresse.
        async with runtime.sessionmaker() as session:
            assert request["id"] not in await accounts.account_ids(session)
            user = await session.get_one(User, request["id"])
            assert user.mail_code is None
        with accounts.use(request["id"]):
            async with secured.sessionmaker() as session:
                assert await session.scalar(text("select count(*) from profiles")) == 0

        # La connexion attend, seulement avec le bon mot de passe.
        waiting = await guest.post(
            "/api/auth/login", json={"username": "camille", "password": PASSWORD}
        )
        assert waiting.status_code == 403
        assert waiting.json()["detail"] == "ton compte attend encore la validation de l'exploitant"
        wrong = await guest.post(
            "/api/auth/login", json={"username": "camille", "password": "pas-le-bon-mot"}
        )
        unknown = await guest.post(
            "/api/auth/login", json={"username": "personne", "password": "pas-le-bon-mot"}
        )
        assert wrong.status_code == unknown.status_code == 401
        assert wrong.json() == unknown.json()
        assert not (await guest.get("/api/auth/me")).json()["authenticated"]

        # Une demande ne se réinitialise ni ne se suspend : elle s'accepte ou se refuse.
        assert (
            await owner.post(f"/api/platform/accounts/{request['id']}/reset")
        ).status_code == 409
        patched = await owner.patch(
            f"/api/platform/accounts/{request['id']}", json={"suspended": True}
        )
        assert patched.status_code == 409

        # Acceptée : le compte devient actif, au plafond par défaut, et le mot est effacé.
        approved = await owner.post(f"/api/platform/accounts/{request['id']}/approve")
        assert approved.status_code == 200
        body = approved.json()
        assert body["signup_requests"] == []
        row = next(a for a in body["accounts"] if a["id"] == request["id"])
        assert row["ai_budget_chf"] == "5" and not row["suspended"]
        async with runtime.sessionmaker() as session:
            user = await session.get_one(User, request["id"])
            assert user.approved_at is not None and user.signup_note is None
            assert request["id"] in await accounts.account_ids(session)
        again = await owner.post(f"/api/platform/accounts/{request['id']}/approve")
        assert again.status_code == 404
        login = await guest.post(
            "/api/auth/login", json={"username": "camille", "password": PASSWORD}
        )
        assert login.status_code == 204
        me = (await guest.get("/api/auth/me")).json()
        assert me["authenticated"] and me["username"] == "camille" and me["welcome"] == "pending"


async def test_request_is_checked(runtime: Runtime, secured: Runtime) -> None:
    async with client(secured) as guest:
        cases = [
            (demand("PROPRIETAIRE"), "déjà pris"),
            (demand(password="court"), "mot de passe refusé"),
            (demand(consent=False), "coche la case"),
            (demand(note="x" * 301), "300"),
            (demand("x" * 41), "40"),
        ]
        for body, expected in cases:
            auth_routes.signup_limit.hits.clear()
            refused = await guest.post("/api/auth/signup", json=body)
            assert refused.status_code == 422, body
            assert expected in refused.text, refused.text
        assert await pending_ids(secured) == []

        # Une demande en attente prend aussi l'identifiant.
        auth_routes.signup_limit.hits.clear()
        assert (await guest.post("/api/auth/signup", json=demand())).status_code == 204
        taken = await guest.post("/api/auth/signup", json=demand("Camille"))
        assert taken.status_code == 422 and "déjà pris" in taken.text


async def test_trap_field_is_ignored_silently(secured: Runtime) -> None:
    async with client(secured) as guest:
        with capture_logs() as logs:
            trapped = await guest.post(
                "/api/auth/signup", json=demand(website="https://spam.example")
            )
        assert trapped.status_code == 204
        assert await pending_ids(secured) == []
        assert [e["event"] for e in logs if e["event"].startswith("signup")] == ["signup_ignored"]


async def test_three_requests_per_hour_and_address(secured: Runtime) -> None:
    async with client(secured) as guest:
        for name in ("a1", "a2", "a3"):
            assert (await guest.post("/api/auth/signup", json=demand(name))).status_code == 204
        blocked = await guest.post("/api/auth/signup", json=demand("a4"))
        assert blocked.status_code == 429 and int(blocked.headers["retry-after"]) > 60
        assert len(await pending_ids(secured)) == 3
    window = service.Window(limit=3, period_s=3600)
    assert [window.take("ip:1") for _ in range(3)] == [0, 0, 0]
    assert window.take("ip:1") > 0 and window.take("ip:2") == 0


async def test_closed_when_full_switched_off_or_demo(runtime: Runtime, secured: Runtime) -> None:
    async with client(runtime) as owner, client(secured) as guest:
        # Éteint par l'exploitant.
        off = await owner.put("/api/platform/settings", json={"signup_open": False})
        assert off.status_code == 200 and off.json()["signup_open"] is False
        assert (await guest.get("/api/auth/signup")).json() == {"open": False}
        closed = await guest.post("/api/auth/signup", json=demand())
        assert closed.status_code == 403
        assert closed.json()["detail"] == "les demandes de compte sont fermées pour le moment"
        # Le plafond de l'IA n'a pas bougé ; il se règle encore seul.
        budget = await owner.put("/api/platform/settings", json={"ai_total_budget_chf": 40})
        assert budget.json()["ai_total_budget_chf"] == "40" and not budget.json()["signup_open"]
        await owner.put("/api/platform/settings", json={"signup_open": True})
        assert (await guest.get("/api/auth/signup")).json() == {"open": True}

        # 20 demandes en attente : fermées.
        async with admin_engine().begin() as conn:
            for i in range(signup.MAX_PENDING):
                await conn.execute(
                    text(
                        "INSERT INTO users (username, password_hash, approved_at) "
                        "VALUES (:u, 'x', NULL)"
                    ),
                    {"u": f"attente-{i}"},
                )
        assert (await guest.get("/api/auth/signup")).json() == {"open": False}
        assert (await guest.post("/api/auth/signup", json=demand())).status_code == 403
        # Elles ne comptent pas parmi les comptes, ni dans le plafond de l'IA.
        listed = (await owner.get("/api/platform")).json()
        assert len(listed["signup_requests"]) == signup.MAX_PENDING
        assert not any(a["username"].startswith("attente-") for a in listed["accounts"])
        assert listed["ai_month_spend_chf"] == "0.00"

    # La démo n'a pas d'inscription.
    demo = Runtime.create(make_settings(auth_enabled=True, demo=True))
    try:
        assert not await signup.is_open(demo)
        async with client(demo) as visitor:
            refused = await visitor.post("/api/auth/signup", json=demand("demo"))
            assert refused.status_code == 403 and refused.json()["demo"] is True
    finally:
        await demo.dispose()


async def test_closed_before_the_owner_is_set_up(secured: Runtime) -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(text("UPDATE users SET password_hash = '!'"))
    async with client(secured) as guest:
        assert (await guest.get("/api/auth/signup")).json() == {"open": False}


async def test_refuse_and_owner_only(runtime: Runtime, secured: Runtime) -> None:
    async with client(runtime) as owner, client(secured) as guest:
        assert (await guest.post("/api/auth/signup", json=demand("refuse"))).status_code == 204
        assert (await guest.post("/api/auth/signup", json=demand("autre"))).status_code == 204
        refused_id, other_id = await pending_ids(secured)
        # Un invité accepté ne touche pas aux demandes.
        token = (await owner.post("/api/platform/invitations")).json()["token"]
        used = await guest.post(
            f"/api/auth/links/{token}", json={"username": "invite", "password": PASSWORD}
        )
        assert used.status_code == 204
        assert (await guest.post(f"/api/platform/accounts/{other_id}/approve")).status_code == 403
        assert (await guest.delete(f"/api/platform/accounts/{other_id}")).status_code == 403
        assert (
            await guest.put("/api/platform/settings", json={"signup_open": False})
        ).status_code == 403
        # Le compte invité est accepté d'office.
        async with runtime.sessionmaker() as session:
            invited = await session.scalar(select(User).where(User.username == "invite"))
            assert invited is not None and invited.approved_at is not None

        # Refusée : la demande et le compte sont effacés.
        deleted = await owner.delete(f"/api/platform/accounts/{refused_id}")
        assert deleted.status_code == 200
        assert [r["id"] for r in deleted.json()["signup_requests"]] == [other_id]
        async with runtime.sessionmaker() as session:
            assert await session.get(User, refused_id) is None


async def test_pending_session_is_refused(runtime: Runtime, secured: Runtime) -> None:
    """Une session, même posée à la main, ne vaut rien pour un compte en attente."""
    async with client(secured) as guest:
        assert (await guest.post("/api/auth/signup", json=demand())).status_code == 204
        [pending] = await pending_ids(secured)
        async with runtime.sessionmaker.begin() as session:
            token = await service.create_session(session, pending, "test")
        guest.cookies.set(service.COOKIE, token)
        assert not (await guest.get("/api/auth/me")).json()["authenticated"]
        assert (await guest.get("/api/offers")).status_code == 401
        async with runtime.sessionmaker() as session:
            assert await session.scalar(select(User.id).join(UserSession)) is not None


async def test_unanswered_requests_are_deleted_after_30_days(
    runtime: Runtime, secured: Runtime
) -> None:
    async with admin_engine().begin() as conn:
        for name, age, approved in (
            ("vieille", "31 days", False),
            ("recente", "10 days", False),
            ("ancien-compte", "60 days", True),
        ):
            await conn.execute(
                text(
                    "INSERT INTO users (username, password_hash, created_at, approved_at) "
                    "VALUES (:u, 'x', now() - cast(:age as interval), "
                    "CASE WHEN :ok THEN now() ELSE NULL END)"
                ),
                {"u": name, "age": age, "ok": approved},
            )
        guest = await conn.scalar(text("SELECT id FROM users WHERE username = 'ancien-compte'"))
    # Au tour d'un autre compte, rien n'est effacé : lui ne voit pas les demandes.
    with accounts.use(int(guest)):
        assert await signup.purge(runtime) == 0
    assert await signup.purge(runtime) == 1
    async with runtime.sessionmaker() as session:
        names = set(await session.scalars(select(User.username)))
    assert {"recente", "ancien-compte"} <= names and "vieille" not in names


async def test_existing_accounts_are_approved_by_the_migration() -> None:
    async with admin_engine().connect() as conn:
        missing = await conn.scalar(
            text("SELECT count(*) FROM users WHERE approved_at IS NULL AND signup_note IS NULL")
        )
    assert missing == 0
