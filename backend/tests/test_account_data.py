"""Tes données (docs/65 §6) : l'export ne contient que le compte, la suppression efface tout,
les mentions de l'exploitant sont publiques et ne se changent que par lui."""

import io
import json
import zipfile
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.db.models import Document, Offer, Search, User
from jobbot.runtime import Runtime

from .conftest import make_settings

PASSWORD = "un-mot-de-passe-solide"
NOW = datetime(2026, 10, 16, 9, tzinfo=UTC)


@pytest.fixture
async def secured(tmp_path: object) -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(auth_enabled=True, storage_path=tmp_path))
    yield runtime
    async with runtime.engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = 'camille-donnees'"))
        await conn.execute(text("DELETE FROM offers WHERE fingerprint LIKE 'donnees-%'"))
        await conn.execute(text("DELETE FROM platform_settings"))
    await runtime.dispose()


async def seed(runtime: Runtime, account: int, marker: str) -> None:
    key = f"accounts/{account}/documents/cv.txt"
    runtime.storage.put(key, f"CV {marker}".encode())
    runtime.storage.put(f"accounts/{account}/emails/a.eml", f"Subject: {marker}".encode())
    with accounts.use(account):
        async with runtime.sessionmaker.begin() as session:
            session.add(
                Offer(
                    fingerprint=f"donnees-{marker}",
                    title=f"Poste {marker}",
                    first_seen_at=NOW,
                    last_seen_at=NOW,
                )
            )
            session.add(
                Document(
                    filename=f"CV {marker}.txt",
                    doc_type="txt",
                    size=3,
                    sha256=marker.ljust(64, "0"),
                    storage_key=key,
                    text_status="ok",
                )
            )
            session.add(
                Search(
                    source="jobup",
                    message_id=f"<{marker}@x>",
                    received_at=NOW,
                    raw_key=f"accounts/{account}/emails/a.eml",
                    parse_status="empty",
                )
            )


async def guest(runtime: Runtime) -> int:
    async with runtime.sessionmaker.begin() as session:
        user = User(username="camille-donnees", password_hash=passwords.hash_password(PASSWORD))
        session.add(user)
        await session.flush()
        return user.id


def client(runtime: Runtime) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=create_app(runtime.settings, runtime)),
        base_url="http://localhost",
    )


async def login(api: AsyncClient) -> None:
    done = await api.post(
        "/api/auth/login", json={"username": "camille-donnees", "password": PASSWORD}
    )
    assert done.status_code == 204


async def test_export_holds_only_the_account(secured: Runtime, account: int) -> None:
    camille = await guest(secured)
    await seed(secured, account, "SECRET-A")
    await seed(secured, camille, "CAMILLE")
    async with client(secured) as api:
        await login(api)
        summary = (await api.get("/api/account/data")).json()
        assert (summary["offers"], summary["documents"], summary["alert_emails"]) == (1, 1, 1)
        assert summary["can_delete"]
        exported = await api.get("/api/account/export")
    assert exported.headers["content-type"] == "application/zip"
    assert "jobA1-camille-donnees-" in exported.headers["content-disposition"]
    archive = zipfile.ZipFile(io.BytesIO(exported.content))
    names = archive.namelist()
    assert "LISEZ-MOI.txt" in names and "data/offers.json" in names
    everything = b"".join(archive.read(n) for n in names)
    assert b"CAMILLE" in everything and b"SECRET-A" not in everything
    offers = json.loads(archive.read("data/offers.json"))
    assert [o["title"] for o in offers] == ["Poste CAMILLE"] and "user_id" not in offers[0]
    document = next(n for n in names if n.startswith("documents/"))
    assert archive.read(document) == b"CV CAMILLE"
    assert [n for n in names if n.startswith("emails/")]


async def test_guest_deletes_own_account(secured: Runtime, account: int) -> None:
    camille = await guest(secured)
    await seed(secured, camille, "CAMILLE")
    async with client(secured) as api:
        await login(api)
        wrong = await api.post("/api/account/delete", json={"password": "pas-le-bon"})
        assert wrong.status_code == 403
        done = await api.post("/api/account/delete", json={"password": PASSWORD})
        assert done.status_code == 204 and "Max-Age=0" in done.headers["set-cookie"]
        assert (await api.get("/api/offers")).status_code == 401
    assert not secured.storage.exists(f"accounts/{camille}/documents/cv.txt")
    async with secured.engine.begin() as conn:
        left = await conn.execute(text("select count(*) from users where id = :c"), {"c": camille})
        assert left.scalar() == 0


async def test_owner_cannot_delete_from_the_platform(runtime: Runtime) -> None:
    async with client(runtime) as api:
        refused = await api.post("/api/account/delete", json={"password": "x"})
        assert refused.status_code == 409
        assert not (await api.get("/api/account/data")).json()["can_delete"]


async def test_privacy_text_public_and_set_by_owner(runtime: Runtime, secured: Runtime) -> None:
    async with client(runtime) as owner:
        saved = await owner.put(
            "/api/privacy", json={"contact": "Kevin, Lausanne. Hébergé chez moi."}
        )
        assert saved.json() == {"contact": "Kevin, Lausanne. Hébergé chez moi."}
    await guest(secured)
    async with client(secured) as api:
        # Sans connexion : lisible.
        assert (await api.get("/api/privacy")).json()["contact"].startswith("Kevin")
        await login(api)
        assert (await api.put("/api/privacy", json={"contact": "autre"})).status_code == 403
