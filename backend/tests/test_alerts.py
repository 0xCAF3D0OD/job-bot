"""Mes alertes (docs/20 §1) : recherches proposées, liens par site, état d'après le journal."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update

from jobbot.api.app import create_app
from jobbot.core.filter import Criteria
from jobbot.db.models import AlertSetup, Search
from jobbot.filtering.service import save_criteria
from jobbot.runtime import Runtime
from jobbot.settings import Settings

RESET = [
    "TRUNCATE alert_searches, searches CASCADE",
    "DELETE FROM settings WHERE key = 'alert_searches_proposed'",
    "UPDATE profiles SET preferences = '{}'::jsonb WHERE is_main",
]


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with runtime.engine.begin() as conn:
        for statement in RESET:
            await conn.execute(text(statement))
        await conn.execute(text("TRUNCATE criteria"))
        await conn.execute(
            text("UPDATE profiles SET preferences = CAST(:p AS jsonb) WHERE is_main").bindparams(
                p='{"domain_keywords": ["DevOps", "Kubernetes"]}'
            )
        )
    async with runtime.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(locations=("Lausanne", "VD", "Genève")))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.engine.begin() as conn:
        for statement in RESET:
            await conn.execute(text(statement))
        await conn.execute(text("TRUNCATE criteria"))


async def add_alert(runtime: Runtime, source: str, label: str, days_ago: int = 1) -> None:
    async with runtime.sessionmaker.begin() as session:
        session.add(
            Search(
                source=source,
                message_id=f"<{source}-{label}-{days_ago}@test>",
                received_at=datetime.now(UTC) - timedelta(days=days_ago),
                subject=f"Nouvelles offres : {label}",
                alert_label=label,
                raw_key="emails/test.eml",
                parse_status="parsed",
            )
        )


async def test_proposed_once_with_links(api: AsyncClient) -> None:
    page = (await api.get("/api/alert-searches")).json()
    # Chaque mot-clé de « Mon domaine » avec chaque lieu (le canton « VD » est écarté).
    assert [(s["terms"], s["location"]) for s in page["searches"]] == [
        ("DevOps", "Lausanne"),
        ("DevOps", "Genève"),
        ("Kubernetes", "Lausanne"),
        ("Kubernetes", "Genève"),
    ]
    urls = {c["site"]: c["url"] for c in page["searches"][0]["cells"]}
    assert urls["jobup"] == "https://www.jobup.ch/fr/emplois/?term=DevOps&location=Lausanne"
    assert urls["jobsch"] == "https://www.jobs.ch/fr/offres-emplois/?term=DevOps&location=Lausanne"
    assert (
        urls["linkedin"]
        == "https://www.linkedin.com/jobs/search/?keywords=DevOps&location=Lausanne"
    )
    assert urls["indeed"] == "https://ch-fr.indeed.com/jobs?q=DevOps&l=Lausanne"
    assert {s["slug"] for s in page["sites"] if s["prefilled"]} >= {"jobup", "jobsch", "linkedin"}
    assert page["mailbox"] is None  # collecte non configurée dans les tests
    # Supprimées, elles ne reviennent pas.
    for search in page["searches"]:
        await api.delete(f"/api/alert-searches/{search['id']}")
    assert (await api.get("/api/alert-searches")).json()["searches"] == []


async def test_status_and_crud(api: AsyncClient, runtime: Runtime) -> None:
    page = (await api.get("/api/alert-searches")).json()
    devops = page["searches"][0]
    for search in page["searches"][1:]:
        await api.delete(f"/api/alert-searches/{search['id']}")

    def cell(page: dict, site: str) -> dict:
        return next(c for c in page["searches"][0]["cells"] if c["site"] == site)

    assert cell(page, "jobup")["status"] == "todo"
    created = (await api.put(f"/api/alert-searches/{devops['id']}/sites/jobup")).json()
    assert cell(created, "jobup")["status"] == "created"
    assert (await api.put(f"/api/alert-searches/{devops['id']}/sites/inconnu")).status_code == 404

    # Rien reçu depuis 4 jours : rappel sur Aujourd'hui.
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(AlertSetup).values(created_at=datetime.now(UTC) - timedelta(days=4))
        )
    assert (await api.get("/api/today")).json()["alerts_waiting"] == 1

    await add_alert(runtime, "jobup", "Ingénieur DevOps Lausanne")
    await add_alert(runtime, "indeed", "Kubernetes")  # autre site, autres mots
    received = (await api.get("/api/alert-searches")).json()
    assert (
        cell(received, "jobup")["status"] == "received" and cell(received, "jobup")["received_at"]
    )
    assert cell(received, "indeed")["status"] == "todo"
    assert (await api.get("/api/today")).json()["alerts_waiting"] == 0

    added = await api.post(
        "/api/alert-searches", json={"terms": "  Platform   engineer ", "location": ""}
    )
    new = next(s for s in added.json()["searches"] if s["terms"] == "Platform engineer")
    assert new["location"] is None
    assert next(c for c in new["cells"] if c["site"] == "jobup")["url"].endswith(
        "?term=Platform+engineer"
    )
    paused = await api.patch(
        f"/api/alert-searches/{new['id']}", json={"active": False, "location": "Sion"}
    )
    after = next(s for s in paused.json()["searches"] if s["id"] == new["id"])
    assert after["active"] is False and after["location"] == "Sion"
    unmarked = (await api.delete(f"/api/alert-searches/{devops['id']}/sites/jobup")).json()
    assert cell(unmarked, "jobup")["status"] == "received"  # l'alerte reçue compte toujours
