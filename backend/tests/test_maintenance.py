"""La plateforme en maintenance (docs/79)."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot import maintenance
from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.db.models import User
from jobbot.db.schema import head_revision
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings

GUEST = "compte-maintenance"
PASSWORD = "un-mot-de-passe-de-test"


@pytest.fixture(autouse=True)
def no_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(maintenance, "CACHE_S", 0.0)


@pytest.fixture
async def guest(runtime: Runtime) -> AsyncIterator[None]:
    async def clean() -> None:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": GUEST})
            await conn.execute(text("DELETE FROM platform_settings WHERE key = 'maintenance'"))

    await clean()
    async with runtime.sessionmaker.begin() as session:
        session.add(User(username=GUEST, password_hash=passwords.hash_password(PASSWORD)))
    yield
    await clean()


async def secured_client() -> AsyncIterator[AsyncClient]:
    secured = Runtime.create(make_settings(auth_enabled=True))
    app = create_app(secured.settings, secured)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://localhost"
        ) as client:
            yield client
    finally:
        await secured.dispose()


async def test_announced_maintenance_lets_only_the_owner_through(
    client: AsyncClient, runtime: Runtime, guest: None
) -> None:
    assert (await client.get("/api/maintenance")).json()["active"] is False
    async with runtime.sessionmaker.begin() as session:
        await maintenance.announce(session, "Nouvelle version, dix minutes")
    # L'exploitant (l'API sans connexion agit en son nom) passe, et le sait.
    assert (await client.get("/api/applications")).status_code == 200
    state = (await client.get("/api/maintenance")).json()
    assert state == {
        "active": True,
        "reason": "announced",
        "mode": "complete",
        "message": "Nouvelle version, dix minutes",
        "bypass": True,
    }
    async for api in secured_client():
        # Un invité se connecte encore, mais attend : 503, avec le message.
        login = await api.post("/api/auth/login", json={"username": GUEST, "password": PASSWORD})
        assert login.status_code == 204
        waiting = await api.get("/api/applications")
        assert waiting.status_code == 503
        assert waiting.headers["retry-after"] == "10"
        assert waiting.json()["maintenance"] is True
        assert waiting.json()["message"] == "Nouvelle version, dix minutes"
        assert (await api.get("/api/maintenance")).json()["bypass"] is False
        # Sans session non plus : l'état reste lisible, le reste attend.
        assert (await api.get("/healthz")).status_code == 200
        async with runtime.sessionmaker.begin() as session:
            await maintenance.lift(session)
        assert (await api.get("/api/applications")).status_code == 200


async def test_database_not_yet_updated_is_a_maintenance_for_everyone(
    client: AsyncClient,
) -> None:
    """Entre `git pull` et `jobbot migrate` : tout attend, l'exploitant aussi (docs/79 §1)."""
    async with admin_engine().begin() as conn:
        await conn.execute(text("UPDATE alembic_version SET version_num = '0001'"))
    try:
        refused = await client.get("/api/applications")
        assert refused.status_code == 503 and refused.json()["reason"] == "update"
        state = (await client.get("/api/maintenance")).json()
        assert state["active"] is True and state["reason"] == "update"
        assert state["bypass"] is False
        assert (await client.post("/api/auth/logout")).status_code == 204
    finally:
        async with admin_engine().begin() as conn:
            await conn.execute(
                text("UPDATE alembic_version SET version_num = :h"), {"h": head_revision()}
            )
    assert (await client.get("/api/applications")).status_code == 200


async def test_unreachable_database_is_not_a_maintenance(offline_client: AsyncClient) -> None:
    """Une base injoignable n'est pas une mise à jour : l'état de la plateforme l'explique."""
    assert (await offline_client.get("/api/maintenance")).json()["active"] is False
    assert (await offline_client.get("/api/status")).status_code == 200


async def test_read_only_maintenance_lets_guests_read(
    client: AsyncClient, runtime: Runtime, guest: None
) -> None:
    """En lecture seule (docs/80), un invité consulte encore ; ses écritures attendent."""
    async with runtime.sessionmaker.begin() as session:
        await maintenance.announce(session, "Sauvegarde", "lecture")
    state = (await client.get("/api/maintenance")).json()
    assert state["mode"] == "lecture" and state["bypass"] is True
    # L'exploitant écrit.
    assert (await client.put("/api/criteria", json={})).status_code != 503
    async for api in secured_client():
        login = await api.post("/api/auth/login", json={"username": GUEST, "password": PASSWORD})
        assert login.status_code == 204
        assert (await api.get("/api/applications")).status_code == 200
        refused = await api.post("/api/news/seen")
        assert refused.status_code == 503
        assert refused.json()["mode"] == "lecture"
        assert refused.json()["message"] == "Sauvegarde"


async def test_background_tasks_wait_except_the_owners(
    runtime: Runtime, account: int, guest: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pendant une maintenance annoncée, la vraie file : la tâche de l'invité et la tâche
    planifiée attendent, celle de l'exploitant passe (docs/80 §3)."""
    from jobbot import accounts
    from jobbot.worker import jobs
    from jobbot.worker.app import build_procrastinate_app
    from jobbot.worker.queue import enqueue

    seen: list[int | None] = []

    async def record(_runtime: Runtime, _ctx: jobs.RunContext) -> None:
        seen.append(accounts.current())

    monkeypatch.setitem(jobs.JOBS, "test-pause", jobs.JobSpec("test-pause", record))
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM procrastinate_jobs"))
        guest_id = await conn.scalar(text("SELECT id FROM users WHERE username = :u"), {"u": GUEST})
    async with runtime.sessionmaker.begin() as session:
        await maintenance.announce(session, None, "lecture")
    assert await maintenance.worker_paused(runtime, None)
    with accounts.use(guest_id):
        assert await enqueue(runtime.settings, "test-pause")
    assert await enqueue(runtime.settings, "test-pause")
    worker = Runtime.create(runtime.settings, "worker")
    try:
        app = build_procrastinate_app(worker)
        async with app.open_async():
            await app.run_worker_async(
                queues=["default"], wait=False, install_signal_handlers=False
            )
    finally:
        await worker.dispose()
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM job_runs WHERE job = 'test-pause'"))
    assert seen == [account]
    async with runtime.sessionmaker.begin() as session:
        await maintenance.lift(session)
    assert not await maintenance.worker_paused(runtime, None)
