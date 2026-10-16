"""Comptes invités (docs/65 §2, §4, §5) : invitation, réinitialisation, suspension,
suppression, plafonds de l'IA, notifications à soi, rubrique Plateforme réservée."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.db.models import LlmCall, User
from jobbot.notify import service as notify_service
from jobbot.runtime import Runtime

from .conftest import make_settings

PASSWORD = "un-mot-de-passe-solide"


@pytest.fixture
async def secured() -> AsyncIterator[Runtime]:
    """Connexion activée : les comptes invités se connectent par leur cookie."""
    runtime = Runtime.create(make_settings(auth_enabled=True))
    yield runtime
    async with runtime.engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE id <> (SELECT min(id) FROM users)"))
        await conn.execute(text("TRUNCATE account_links, platform_settings"))
    await runtime.dispose()


def client(runtime: Runtime) -> AsyncClient:
    app = create_app(runtime.settings, runtime)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


async def invite(owner: AsyncClient, guest: AsyncClient, username: str = "camille") -> int:
    token = (await owner.post("/api/platform/invitations")).json()["token"]
    used = await guest.post(
        f"/api/auth/links/{token}", json={"username": username, "password": PASSWORD}
    )
    assert used.status_code == 204, used.text
    return await account_id(owner, username)


async def account_id(owner: AsyncClient, username: str) -> int:
    found = (await owner.get("/api/platform")).json()["accounts"]
    return int(next(a["id"] for a in found if a["username"] == username))


async def test_invitation_creates_an_account_with_its_own_profile(
    runtime: Runtime, secured: Runtime
) -> None:
    async with client(runtime) as owner, client(secured) as guest:
        created = await owner.post("/api/platform/invitations")
        assert created.status_code == 201
        token = created.json()["token"]
        listed = (await owner.get("/api/platform")).json()
        assert [i["id"] for i in listed["invitations"]] == [created.json()["id"]]

        link = (await guest.get(f"/api/auth/links/{token}")).json()
        assert link["kind"] == "invite" and link["username"] is None
        weak = await guest.post(
            f"/api/auth/links/{token}", json={"username": "c", "password": "court"}
        )
        assert weak.status_code == 422
        taken = await guest.post(
            f"/api/auth/links/{token}", json={"username": "PROPRIETAIRE", "password": PASSWORD}
        )
        assert taken.status_code == 422 and "déjà pris" in taken.text
        used = await guest.post(
            f"/api/auth/links/{token}", json={"username": "camille", "password": PASSWORD}
        )
        assert used.status_code == 204
        me = (await guest.get("/api/auth/me")).json()
        assert me["authenticated"] and me["username"] == "camille" and not me["is_owner"]
        # Un lien ne sert qu'une fois.
        again = await guest.post(
            f"/api/auth/links/{token}", json={"username": "autre", "password": PASSWORD}
        )
        assert again.status_code == 410
        assert (await guest.get("/api/auth/links/jba_inconnu")).status_code == 404

        # Son profil principal suit d'office les articles « marché de l'emploi ».
        camille = await account_id(owner, "camille")
        with accounts.use(camille):
            async with secured.sessionmaker() as session:
                assert await session.scalar(text("select count(*) from profiles")) == 1
                assert await session.scalar(text("select count(*) from profile_sources")) > 0

        # La rubrique Plateforme lui est fermée, comme les profils d'essai.
        assert (await guest.get("/api/platform")).status_code == 403
        assert (await guest.post("/api/platform/invitations")).status_code == 403
        trial = await guest.post("/api/profiles", json={"name": "Essai"})
        assert trial.status_code == 403
        # Ce qu'en voit l'exploitant : l'usage, sans ses données.
        row = next(
            a for a in (await owner.get("/api/platform")).json()["accounts"] if a["id"] == camille
        )
        assert row["month_offers"] == 0 and row["month_spend_chf"] == "0.00"
        assert row["ai_budget_chf"] == "5" and row["last_login_at"] and not row["suspended"]


async def test_expired_invitation(runtime: Runtime, secured: Runtime) -> None:
    async with client(runtime) as owner, client(secured) as guest:
        token = (await owner.post("/api/platform/invitations")).json()["token"]
        async with runtime.engine.begin() as conn:
            await conn.execute(text("UPDATE account_links SET expires_at = now() - interval '1 s'"))
        assert (await guest.get(f"/api/auth/links/{token}")).status_code == 410
        assert (await owner.get("/api/platform")).json()["invitations"] == []


async def test_reset_suspend_and_delete(runtime: Runtime, secured: Runtime) -> None:
    async with client(runtime) as owner, client(secured) as guest:
        camille = await invite(owner, guest)
        # Réinitialisation : un nouveau mot de passe, les autres sessions fermées.
        async with client(secured) as other_device:
            login = await other_device.post(
                "/api/auth/login", json={"username": "camille", "password": PASSWORD}
            )
            assert login.status_code == 204
            reset = (await owner.post(f"/api/platform/accounts/{camille}/reset")).json()
            link = (await guest.get(f"/api/auth/links/{reset['token']}")).json()
            assert link == {
                "kind": "reset",
                "username": "camille",
                "expires_at": link["expires_at"],
            }
            changed = await guest.post(
                f"/api/auth/links/{reset['token']}", json={"password": PASSWORD + "-2"}
            )
            assert changed.status_code == 204
            assert not (await other_device.get("/api/auth/me")).json()["authenticated"]
        assert (await guest.get("/api/auth/me")).json()["username"] == "camille"

        # Suspendu : sa session ne vaut plus, il ne se connecte plus, aucune tâche pour lui.
        await owner.patch(f"/api/platform/accounts/{camille}", json={"suspended": True})
        assert (await guest.get("/api/offers")).status_code == 401
        refused = await guest.post(
            "/api/auth/login", json={"username": "camille", "password": PASSWORD + "-2"}
        )
        assert refused.status_code == 403 and "suspendu" in refused.text
        async with runtime.sessionmaker() as session:
            assert camille not in await accounts.account_ids(session)
        await owner.patch(f"/api/platform/accounts/{camille}", json={"suspended": False})

        # L'exploitant ne se suspend ni ne se supprime.
        owner_id = await account_id(owner, "proprietaire")
        assert (await owner.delete(f"/api/platform/accounts/{owner_id}")).status_code == 409

        # Supprimé : le compte, ses données et ses fichiers.
        secured.storage.put(f"accounts/{camille}/documents/cv.pdf", b"%PDF")
        with accounts.use(camille):
            async with secured.sessionmaker.begin() as session:
                session.add(LlmCall(purpose="test", model="m", cost_usd=1, cost_chf=Decimal("0.8")))
        deleted = await owner.delete(f"/api/platform/accounts/{camille}")
        assert deleted.status_code == 200
        assert camille not in [a["id"] for a in deleted.json()["accounts"]]
        assert not secured.storage.exists(f"accounts/{camille}/documents/cv.pdf")
        async with runtime.engine.begin() as conn:
            left = await conn.execute(
                text("select count(*) from llm_calls where user_id = :c"), {"c": camille}
            )
            assert left.scalar() == 0


async def test_ai_caps_per_account_and_platform(runtime: Runtime, secured: Runtime) -> None:
    async with client(runtime) as owner, client(secured) as guest:
        camille = await invite(owner, guest)
        await owner.patch(f"/api/platform/accounts/{camille}", json={"ai_budget_chf": 2})
        assert (await guest.get("/api/settings")).json()["llm_monthly_budget_chf"] == 2
        body = (await guest.get("/api/settings")).json() | {"llm_monthly_budget_chf": 99}
        assert (await guest.put("/api/settings", json=body)).json()["llm_monthly_budget_chf"] == 2
        status = (await guest.get("/api/scoring")).json()
        assert (status["budget_chf"], status["budget_reached"]) == ("2.00", False)

        # Le plafond total, tous comptes confondus, arrête aussi le compte.
        with accounts.use(camille):
            async with secured.sessionmaker.begin() as session:
                session.add(LlmCall(purpose="test", model="m", cost_usd=1, cost_chf=Decimal("1")))
        platform = await owner.put("/api/platform/settings", json={"ai_total_budget_chf": 1})
        assert platform.json()["ai_month_spend_chf"] == "1.00"
        status = (await guest.get("/api/scoring")).json()
        assert status["budget_reached"] and status["platform_budget_reached"]
        # Le plafond de l'exploitant reste celui de ses Réglages.
        assert (await owner.get("/api/settings")).json()["llm_monthly_budget_chf"] == 10


async def test_phone_notifications_are_per_account(
    runtime: Runtime, secured: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[str] = []

    async def capture(settings: object, _message: object) -> None:
        topic = getattr(settings, "ntfy_topic", None)
        sent.append(topic.get_secret_value() if topic else "")

    monkeypatch.setattr(notify_service, "send", capture)
    async with client(runtime) as owner, client(secured) as guest:
        camille = await invite(owner, guest)
        status = (await guest.get("/api/notifications")).json()
        assert status["personal"] and not status["configured"] and status["topic"] is None
        message = notify_service.Message(title="t", message="m")
        with accounts.use(camille):
            await notify_service.deliver(secured, message, kind="test", link="/")
        assert sent == []  # pas activé : seulement dans la cloche

        enabled = (await guest.put("/api/notifications/phone", json={"enabled": True})).json()
        assert enabled["configured"] and enabled["topic"].startswith("jobbot-")
        with accounts.use(camille):
            await notify_service.deliver(secured, message, kind="test", link="/")
        assert sent == [enabled["topic"]]
        assert (await guest.post("/api/notifications/test")).status_code == 204
        assert sent[-1] == enabled["topic"]
        off = (await guest.put("/api/notifications/phone", json={"enabled": False})).json()
        assert not off["configured"] and off["topic"] is None
        # L'exploitant garde le sujet de l'installation, réglé dans le README.
        assert (
            await owner.put("/api/notifications/phone", json={"enabled": True})
        ).status_code == 409


async def test_jobs_skip_suspended_accounts(runtime: Runtime, secured: Runtime) -> None:
    async with client(runtime) as owner, client(secured) as guest:
        camille = await invite(owner, guest)
        async with runtime.sessionmaker() as session:
            assert camille in await accounts.account_ids(session)
        async with runtime.sessionmaker.begin() as session:
            user = await session.scalar(select(User).where(User.id == camille))
            assert user is not None
            user.suspended_at = datetime.now(UTC) - timedelta(minutes=1)
        async with runtime.sessionmaker() as session:
            assert camille not in await accounts.account_ids(session)
