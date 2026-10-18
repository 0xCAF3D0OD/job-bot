"""Revue page par page (docs/43) : ce qui passe en tête d'Aujourd'hui."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.db.models import Application
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import admin_engine

TRUNCATE = "TRUNCATE offers, applications CASCADE"


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))


async def test_upcoming_interviews_come_first(api: AsyncClient, runtime: Runtime) -> None:
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        for company, at, status in [
            ("Bientôt SA", now + timedelta(hours=3), "entretien"),
            ("Plus tard SA", now + timedelta(days=4), "entretien"),
            ("Refusée SA", now + timedelta(hours=5), "refus"),
            ("Passée SA", now - timedelta(hours=2), "entretien"),
        ]:
            session.add(
                Application(
                    sent_at=date.today() - timedelta(days=10),
                    method="electronique",
                    company=company,
                    job_title="SRE",
                    orp_month=f"{date.today():%Y-%m}",
                    status=status,
                    interview_at=at,
                )
            )
    upcoming = (await api.get("/api/today")).json()["upcoming_interviews"]
    assert [u["company"] for u in upcoming] == ["Bientôt SA"]
