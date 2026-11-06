"""Le formulaire « Créer une alerte » des sites, depuis l'extension (docs/142 §4) : l'adresse jobA1
du compte, et « J'ai créé l'alerte » comme le bouton de l'assistant des alertes."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from structlog.testing import capture_logs

from jobbot.api.app import create_app
from jobbot.db.models import AlertSearch, AlertSetup
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings


@pytest.fixture
async def mailbox() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(imap_user="alertes@joba1.ch", imap_password="x"))
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE extension_tokens, alert_searches, searches CASCADE"))
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE extension_tokens, alert_searches, searches CASCADE"))
    await runtime.dispose()


@pytest.fixture
async def api(mailbox: Runtime) -> AsyncIterator[tuple[AsyncClient, dict[str, str]]]:
    app = create_app(mailbox.settings, mailbox)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = (await client.post("/api/extension-tokens", json={"name": "Firefox"})).json()
        yield client, {"Authorization": f"Bearer {token['token']}"}


async def searches(rt: Runtime, *terms: str, active: bool = True) -> list[int]:
    async with rt.sessionmaker.begin() as session:
        rows = [AlertSearch(terms=t, location="Lausanne", active=active) for t in terms]
        session.add_all(rows)
        await session.flush()
        return [r.id for r in rows]


async def setups(rt: Runtime) -> set[tuple[int, str]]:
    async with rt.sessionmaker() as session:
        return {(s.search_id, s.site) for s in await session.scalars(select(AlertSetup))}


async def test_address_and_sites_to_do(
    api: tuple[AsyncClient, dict[str, str]], mailbox: Runtime
) -> None:
    client, auth = api
    await searches(mailbox, "DevOps", "SRE")
    await searches(mailbox, "Ancienne", active=False)

    body = (await client.get("/api/extension/alerts", headers=auth)).json()

    assert body["address"] == "alertes@joba1.ch"
    assert body["todo"] == {"jobup": 2, "jobsch": 2, "linkedin": 2}


async def test_alert_created_like_the_wizard(
    api: tuple[AsyncClient, dict[str, str]], mailbox: Runtime
) -> None:
    client, auth = api
    devops, sre = await searches(mailbox, "DevOps", "SRE")
    [old] = await searches(mailbox, "Ancienne", active=False)
    # Déjà marquée depuis l'assistant : pas doublée.
    await client.put(f"/api/alert-searches/{devops}/sites/jobup")

    with capture_logs() as logs:
        response = await client.put("/api/extension/alerts/jobup", headers=auth)

    assert response.status_code == 200
    assert response.json() == {"site": "jobup", "marked": 1}
    assert await setups(mailbox) == {(devops, "jobup"), (sre, "jobup")}
    assert (old, "jobup") not in await setups(mailbox)
    # Le journal : le site et le nombre, sans l'adresse (J-1).
    assert [e for e in logs if e["event"] == "extension_alert_created"] == [
        {"event": "extension_alert_created", "site": "jobup", "searches": 1, "log_level": "info"}
    ]
    after = (await client.get("/api/extension/alerts", headers=auth)).json()
    assert after["todo"]["jobup"] == 0


async def test_only_alert_sites(api: tuple[AsyncClient, dict[str, str]], mailbox: Runtime) -> None:
    client, auth = api
    await searches(mailbox, "DevOps")
    assert (await client.put("/api/extension/alerts/indeed", headers=auth)).status_code == 404
    assert (await client.put("/api/extension/alerts/inconnu", headers=auth)).status_code == 404
    assert await setups(mailbox) == set()


async def test_needs_the_extension_token(api: tuple[AsyncClient, dict[str, str]]) -> None:
    client, _auth = api
    assert (await client.get("/api/extension/alerts")).status_code == 401
    assert (await client.put("/api/extension/alerts/jobup")).status_code == 401
