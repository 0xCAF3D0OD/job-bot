"""Les tests utilisent une vraie base PostgreSQL, distincte de celle de développement.

URL : JOBBOT_TEST_DATABASE_URL, par défaut la base locale `jobbot_test` (créée par `make setup`).
Le schéma public est recréé au début de la session, puis les migrations sont appliquées.
"""

import os
from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text

from jobbot.api.app import create_app
from jobbot.db.schema import upgrade
from jobbot.runtime import Runtime
from jobbot.settings import Settings

TEST_DATABASE_URL = os.environ.get(
    "JOBBOT_TEST_DATABASE_URL", "postgresql+psycopg://localhost:5432/jobbot_test"
)
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://jobbot@127.0.0.1:1/jobbot"


def make_settings(**overrides: object) -> Settings:
    """Configuration de test, indépendante du .env du poste (boîte IMAP comprise)."""
    values: dict[str, object] = {
        "database_url": TEST_DATABASE_URL,
        "version": "test",
        "imap_user": "",
        "imap_password": None,
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.fixture(scope="session")
def settings() -> Settings:
    return make_settings()


@pytest.fixture(scope="session", autouse=True)
def migrated_database(settings: Settings) -> Iterator[None]:
    engine = create_engine(settings.sqlalchemy_url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    upgrade(settings)
    yield


@pytest.fixture(scope="session")
async def runtime(settings: Settings) -> AsyncIterator[Runtime]:
    rt = Runtime.create(settings)
    yield rt
    await rt.dispose()


@pytest.fixture
async def client(settings: Settings, runtime: Runtime) -> AsyncIterator[AsyncClient]:
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def clean_job_runs(runtime: Runtime) -> None:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE job_runs CASCADE"))


@pytest.fixture
async def offline_client() -> AsyncIterator[AsyncClient]:
    """API dont la base est injoignable."""
    settings = make_settings(database_url=UNREACHABLE_DATABASE_URL)
    runtime = Runtime.create(settings)
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await runtime.dispose()
