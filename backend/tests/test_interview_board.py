"""Tableau des retours d'entretien (décision de Kevin du 17.11.2026) : lecture seule."""

import logging
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text
from structlog.testing import capture_logs

from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.db.models import Application, Interview, User
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings

GUEST = "retours-autre"
PASSWORD = "un-mot-de-passe-solide"
SECRET = "Réponse confidentielle sur Kubernetes"


async def reset() -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE applications, interviews, notifications CASCADE"))


async def add_application(
    runtime: Runtime, company: str, interview_at: datetime | None, status: str = "entretien"
) -> int:
    async with runtime.sessionmaker.begin() as session:
        application = Application(
            company=company,
            sent_at=date(2026, 10, 2),
            method="electronique",
            job_title="Ingénieur DevOps",
            orp_month="2026-10",
            status=status,
            interview_at=interview_at,
        )
        session.add(application)
        await session.flush()
        return application.id


async def add_review(client: AsyncClient, application_id: int, **extra: object) -> int:
    body = {"rating": 4, **extra}
    response = await client.post(f"/api/applications/{application_id}/interviews", json=body)
    assert response.status_code == 201
    return int(response.json()["id"])


async def test_lines_states_and_order(client: AsyncClient, runtime: Runtime) -> None:
    await reset()
    now = datetime.now(UTC)
    upcoming = await add_application(runtime, "Avenir SA", now + timedelta(days=3))
    to_do = await add_application(runtime, "Oubli SA", now - timedelta(days=2))
    rejected = await add_application(runtime, "Refus SA", now - timedelta(days=20), "refus")
    hired = await add_application(runtime, "Engage SA", now - timedelta(days=30), "engagement")
    review = await add_review(
        client,
        rejected,
        kind="technique",
        held_at=(now - timedelta(days=20)).date().isoformat(),
        stress=2,
        outlook="unsure",
        next_step="reponse",
        next_step_at=(now - timedelta(days=10)).date().isoformat(),
        thanks="sent",
        questions=[{"text": "Pourquoi ce poste ?"}, {"text": SECRET, "difficult": True}],
        went_well=SECRET,
    )
    await add_review(client, hired, rating=5, thanks="todo")
    # Un second entretien prévu pour une candidature qui a déjà son premier retour.
    second = await add_application(runtime, "Suite SA", now + timedelta(days=5))
    await add_review(client, second, held_at=(now - timedelta(days=1)).date().isoformat())

    body = (await client.get("/api/interviews")).json()
    assert body["total"] == 6
    rows = body["items"]
    assert [(r["company"], r["point"]) for r in rows] == [
        ("Suite SA", "a_venir"),
        ("Avenir SA", "a_venir"),
        ("Suite SA", "fait"),
        ("Oubli SA", "a_faire"),
        ("Refus SA", "fait"),
        ("Engage SA", "fait"),
    ]
    by_company = {(r["company"], r["point"]): r for r in rows}
    done = by_company[("Refus SA", "fait")]
    assert done == {
        "interview_id": review,
        "application_id": rejected,
        "company": "Refus SA",
        "job_title": "Ingénieur DevOps",
        "day": (now - timedelta(days=20)).date().isoformat(),
        "kind": "technique",
        "rating": 4,
        "stress": 2,
        "outlook": "unsure",
        "next_step": "reponse",
        "next_step_at": (now - timedelta(days=10)).date().isoformat(),
        "thanks_sent": True,
        "point": "fait",
        "issue": "pas_retenu",
        "questions_count": 2,
    }
    # Pas de texte libre dans la liste : ni les notes, ni les questions.
    assert SECRET not in str(body)
    assert by_company[("Engage SA", "fait")]["issue"] == "retenu"
    assert by_company[("Engage SA", "fait")]["thanks_sent"] is False
    planned = by_company[("Avenir SA", "a_venir")]
    assert planned["interview_id"] is None and planned["thanks_sent"] is None
    assert planned["issue"] == "en_attente" and planned["application_id"] == upcoming
    assert by_company[("Oubli SA", "a_faire")]["application_id"] == to_do
    await reset()


async def test_pages_of_twenty(client: AsyncClient, runtime: Runtime) -> None:
    await reset()
    start = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
    for n in range(23):
        await add_application(runtime, f"Firme {n:02d}", start + timedelta(days=n))
    first = (await client.get("/api/interviews")).json()
    assert first["total"] == 23 and len(first["items"]) == 20
    assert first["items"][0]["company"] == "Firme 22"
    rest = (await client.get("/api/interviews?offset=20")).json()
    assert [r["company"] for r in rest["items"]] == ["Firme 02", "Firme 01", "Firme 00"]
    assert (await client.get("/api/interviews?offset=-1")).status_code == 422
    await reset()


async def test_detail_is_read_only_and_never_logged(
    client: AsyncClient, runtime: Runtime, caplog: pytest.LogCaptureFixture
) -> None:
    await reset()
    application_id = await add_application(
        runtime, "Détail SA", datetime.now(UTC) - timedelta(days=1)
    )
    review = await add_review(
        client, application_id, went_badly=SECRET, questions=[{"text": SECRET}]
    )
    async with runtime.sessionmaker() as session:
        before = await session.scalar(select(func.max(Interview.updated_at)))
    caplog.set_level(logging.DEBUG)
    with capture_logs() as logs:
        listed = await client.get("/api/interviews")
        detail = await client.get(f"/api/interviews/{review}")
    assert listed.status_code == 200 and detail.status_code == 200
    full = detail.json()
    assert full["went_badly"] == SECRET and full["questions"] == [
        {"text": SECRET, "difficult": False}
    ]
    assert (full["company"], full["point"], full["issue"]) == ("Détail SA", "fait", "en_attente")
    # Rien n'est écrit en lisant.
    async with runtime.sessionmaker() as session:
        assert await session.scalar(select(func.max(Interview.updated_at))) == before
    # Rien du contenu ni de l'identifiant du retour dans les journaux de l'application.
    assert logs, "la capture voit au moins le journal des requêtes"
    server = "\n".join(r.getMessage() for r in caplog.records if r.name != "httpx")
    for captured in (repr(logs), server):
        assert SECRET not in captured
        assert f"/api/interviews/{review}" not in captured
    assert (await client.get("/api/interviews/999999")).status_code == 404
    # « insights » reste la route des enseignements, pas un identifiant.
    assert (await client.get("/api/interviews/insights")).status_code == 200
    await reset()


async def test_another_account_sees_nothing(client: AsyncClient, runtime: Runtime) -> None:
    """C-4 : un autre compte, connecté, reçoit 404 sur le détail et une liste vide."""
    await reset()
    application_id = await add_application(
        runtime, "Secret SA", datetime.now(UTC) - timedelta(days=1)
    )
    review = await add_review(client, application_id, held_at="2026-11-10")
    secured = Runtime.create(make_settings(auth_enabled=True))
    async with secured.sessionmaker.begin() as session:
        session.add(User(username=GUEST, password_hash=passwords.hash_password(PASSWORD)))
    try:
        app = create_app(secured.settings, secured)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://localhost"
        ) as api:
            login = {"username": GUEST, "password": PASSWORD}
            assert (await api.post("/api/auth/login", json=login)).status_code == 204
            assert (await api.get(f"/api/interviews/{review}")).status_code == 404
            # Le point rouvert depuis Rendez-vous (19.11) : ni lu ni modifié par un autre compte.
            assert (await api.get(f"/api/interviews/{review}/debrief")).status_code == 404
            put = await api.put(f"/api/interviews/{review}/debrief", json={"feeling": "bien"})
            assert put.status_code == 404
            # « Ajouter un entretien » (§72p) : rien d'ajouté chez un autre compte.
            plan = {"round": "2", "at": "2026-12-01T13:00:00Z", "place": "Lausanne"}
            added = await api.post(f"/api/applications/{application_id}/interview-plan", json=plan)
            assert added.status_code == 404
            assert (await api.get("/api/interviews")).json() == {"items": [], "total": 0}
    finally:
        async with secured.engine.begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": GUEST})
        await secured.dispose()
    assert (await client.get(f"/api/interviews/{review}")).status_code == 200
    assert (await client.get(f"/api/interviews/{review}/debrief")).status_code == 200
    await reset()
