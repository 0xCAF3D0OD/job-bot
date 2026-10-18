"""La connexion et les protections HTTP (docs/78 §2, version 0.64.2)."""

import io
import zipfile
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.auth.service import SESSION_MAX_AGE, Throttle, authenticate, create_session, token_hash
from jobbot.core.extract import UnsupportedDocument, detect_type
from jobbot.db.models import CalendarToken, ExtensionToken, Offer, OfferStatus, User, UserSession
from jobbot.logos import service as logos
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import admin_engine, make_settings

GUEST = "compte-connexion"
NOW = datetime.now(UTC)


@pytest.fixture
async def guest(runtime: Runtime) -> AsyncIterator[int]:
    async def clean() -> None:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": GUEST})
            await conn.execute(text("TRUNCATE offers, company_logos, companies CASCADE"))

    await clean()
    async with runtime.sessionmaker.begin() as session:
        user = User(username=GUEST, password_hash=passwords.hash_password("x" * 12))
        session.add(user)
        await session.flush()
        guest_id = user.id
    yield guest_id
    await clean()


async def test_suspension_cuts_extension_and_calendar_tokens(
    client: AsyncClient, runtime: Runtime, guest: int
) -> None:
    with accounts.use(guest):
        async with runtime.sessionmaker.begin() as session:
            session.add(ExtensionToken(name="B", token_hash="1" * 64))
            session.add(CalendarToken(name="B", token_hash="2" * 64))

    async def owners() -> tuple[int | None, int | None]:
        async with runtime.sessionmaker() as session:
            return (
                await accounts.account_of_token(session, "extension", "1" * 64),
                await accounts.account_of_token(session, "calendar", "2" * 64),
            )

    assert await owners() == (guest, guest)
    # Suspendu par la base elle-même, même sans passer par la route : ses jetons ne passent plus.
    async with runtime.sessionmaker.begin() as session:
        (await session.get_one(User, guest)).suspended_at = NOW
    assert await owners() == (None, None)
    async with runtime.sessionmaker.begin() as session:
        (await session.get_one(User, guest)).suspended_at = None
    assert (
        await client.patch(f"/api/platform/accounts/{guest}", json={"suspended": True})
    ).status_code == 200
    # La route les révoque aussi : réactivé, le compte devra en créer de nouveaux.
    assert (
        await client.patch(f"/api/platform/accounts/{guest}", json={"suspended": False})
    ).status_code == 200
    assert await owners() == (None, None)


def test_throttle_by_address_not_by_name_alone() -> None:
    """Un inconnu qui rate le mot de passe de quelqu'un ne bloque pas sa connexion ailleurs."""
    throttle = Throttle()
    stranger = ("ip:203.0.113.9", "ip-user:203.0.113.9:kevin")
    for _ in range(8):
        throttle.fail(*stranger)
    assert throttle.wait(*stranger) > 0
    assert throttle.wait("ip:192.0.2.1", "ip-user:192.0.2.1:kevin") == 0
    # Un essai raté est oublié après une journée.
    throttle.failures = {
        k: (count, last - 25 * 3600) for k, (count, last) in throttle.failures.items()
    }
    assert throttle.wait(*stranger) == 0 and throttle.failures == {}


def test_no_login_only_on_ones_own_computer() -> None:
    assert not make_settings(auth_enabled=False).auth_enabled
    for overrides in ({"api_host": "0.0.0.0"}, {"env": "prod"}):
        with pytest.raises(ValueError, match="JOBBOT_AUTH_ENABLED=false"):
            make_settings(auth_enabled=False, **overrides)
    assert make_settings(auth_enabled=True, api_host="0.0.0.0").auth_enabled


async def test_session_ends_ninety_days_after_login(runtime: Runtime, account: int) -> None:
    async with runtime.sessionmaker.begin() as session:
        token = await create_session(session, account, None)
        stored = await session.get_one(UserSession, token_hash(token))
        # Connecté il y a 89 jours, servie hier : prolongée, mais pas au-delà des 90 jours.
        stored.created_at = NOW - SESSION_MAX_AGE + timedelta(days=1)
        stored.last_seen_at = NOW - timedelta(days=2)
        stored.expires_at = NOW + timedelta(hours=1)
    async with runtime.sessionmaker.begin() as session:
        found = await authenticate(session, token)
        assert found is not None and found.renewed
        stored = await session.get_one(UserSession, token_hash(token))
        assert stored.expires_at <= stored.created_at + SESSION_MAX_AGE
        stored.created_at = NOW - SESSION_MAX_AGE - timedelta(minutes=1)
    async with runtime.sessionmaker.begin() as session:
        assert await authenticate(session, token) is None
    async with runtime.sessionmaker() as session:
        assert await session.get(UserSession, token_hash(token)) is None


async def test_address_lookup_is_a_protected_write(client: AsyncClient) -> None:
    path = "/api/offers/1/address-candidates"
    assert (await client.get(path)).status_code == 405
    refused = await client.post(path, headers={"Sec-Fetch-Site": "cross-site"})
    assert refused.status_code == 403


async def test_security_headers_size_limit_and_local_only(settings: Settings) -> None:
    app = create_app(settings, Runtime.create(settings))

    async def call(client: tuple[str, int], method: str, path: str, **kw: Any) -> Any:
        transport = ASGITransport(app=app, client=client)
        async with AsyncClient(transport=transport, base_url="http://test") as api:
            return await api.request(method, path, **kw)

    local, outside = ("127.0.0.1", 50000), ("8.8.8.8", 50000)  # une adresse publique
    response = await call(local, "GET", "/healthz")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert response.headers["referrer-policy"] == "same-origin"
    for path in ("/metrics", "/version", "/readyz"):
        assert (await call(local, "GET", path)).status_code != 404, path
        assert (await call(outside, "GET", path)).status_code == 404, path
        forwarded = await call(local, "GET", path, headers={"X-Forwarded-For": "203.0.113.5"})
        assert forwarded.status_code == 404, path
    assert (await call(outside, "GET", "/healthz")).status_code == 200
    big = await call(
        local,
        "POST",
        "/api/documents",
        headers={"Content-Length": str(12 * 1024 * 1024), "Content-Type": "application/json"},
        content=b"",
    )
    assert big.status_code == 413


async def test_text_document_is_downloaded_not_shown(client: AsyncClient) -> None:
    uploaded = await client.post(
        "/api/documents", files={"file": ("notes.md", b"<script>alert(1)</script>")}
    )
    assert uploaded.status_code in (200, 201), uploaded.text
    served = await client.get(f"/api/documents/{uploaded.json()['id']}/file")
    assert served.headers["content-disposition"] == "attachment"
    assert served.headers["x-content-type-options"] == "nosniff"
    await client.delete(f"/api/documents/{uploaded.json()['id']}")


def test_oversized_docx_is_refused() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", "<w:document/>")
        with archive.open("word/media/zeros.bin", "w", force_zip64=True) as entry:
            chunk = b"\0" * (1024 * 1024)
            for _ in range(101):
                entry.write(chunk)
    with pytest.raises(UnsupportedDocument):
        detect_type("cv.docx", buffer.getvalue())


async def test_guest_typed_site_does_not_choose_the_common_logo(
    runtime: Runtime, guest: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    requested: list[str] = []

    async def fake_get(_client: object, url: str, _limit: int) -> tuple[bytes, str]:
        requested.append(url)
        raise logos.Refused("inconnu")

    monkeypatch.setattr(logos, "_get", fake_get)
    with accounts.use(guest):
        async with runtime.sessionmaker.begin() as session:
            session.add(
                Offer(
                    fingerprint="logo-invite",
                    title="DevOps",
                    company="Delta SA",
                    company_website="https://pirate.example/",
                    first_seen_at=NOW,
                    last_seen_at=NOW,
                    status=OfferStatus.TO_REVIEW,
                )
            )
        # La tâche du worker, avec son accès : elle écrit le logo commun.
        worker = Runtime.create(runtime.settings, "worker")
        try:
            await logos.fetch_logos(worker)
        finally:
            await worker.dispose()
    assert not any("pirate.example" in url for url in requested)
