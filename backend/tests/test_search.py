"""La recherche globale (série du 27.10, point 2) : offres, candidatures, entreprises."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.db.models import Application, Evaluation, Offer
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import admin_engine


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers, applications CASCADE"))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers, applications CASCADE"))


async def seed(runtime: Runtime) -> None:
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        for i, (title, company, score) in enumerate(
            [
                ("DevOps Engineer", "Prototype Fintech SA", 90),
                ("Ingénieur·e DevOps", "Fictif Cloud SA", 75),
                ("DevOps junior", "Banque Exemple", 72),
                ("DevOps senior", "DevOps Partners SA", 60),
                ("Comptable", "DevOps Partners SA", None),
            ]
        ):
            offer = Offer(
                fingerprint=f"f{i}",
                title=title,
                company=company,
                location="Genève",
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(offer)
            await session.flush()
            if score is not None:
                session.add(
                    Evaluation(
                        offer_id=offer.id, filter_passed=True, criteria_hash="x", score=score
                    )
                )
        session.add(
            Application(
                sent_at=date(2026, 10, 12),
                method="electronique",
                company="Démo Data SA",
                job_title="Platform Engineer (DevOps)",
                orp_month="2026-10",
            )
        )


async def test_three_groups_three_hits_and_totals(api: AsyncClient, runtime: Runtime) -> None:
    await seed(runtime)
    found = (await api.get("/api/search", params={"q": "devops"})).json()
    assert found["offers"]["total"] == 5
    assert [o["title"] for o in found["offers"]["items"]] == [
        "DevOps Engineer",
        "Ingénieur·e DevOps",
        "DevOps junior",
    ]
    assert found["applications"]["total"] == 1
    assert found["applications"]["items"][0]["company"] == "Démo Data SA"
    assert found["companies"]["items"][0] == {
        "name": "DevOps Partners SA",
        "offers": 2,
        "applications": 0,
    }


async def test_accents_and_all_words(api: AsyncClient, runtime: Runtime) -> None:
    await seed(runtime)
    accents = (await api.get("/api/search", params={"q": "ingenieur geneve"})).json()
    assert [o["title"] for o in accents["offers"]["items"]] == ["Ingénieur·e DevOps"]
    nothing = (await api.get("/api/search", params={"q": "boulanger"})).json()
    assert (
        nothing["offers"]["total"]
        == nothing["applications"]["total"]
        == nothing["companies"]["total"]
        == 0
    )
