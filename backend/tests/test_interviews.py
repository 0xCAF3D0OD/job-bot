"""Retour d'entretien (docs/23) : formulaire, liste avec la candidature, rappel du lendemain."""

from datetime import UTC, date, datetime

from httpx import AsyncClient
from sqlalchemy import select, text

from jobbot.db.models import Application, Notification
from jobbot.notify.interviews import notify_interviews
from jobbot.runtime import Runtime


async def add_application(runtime: Runtime, **extra: object) -> int:
    async with runtime.sessionmaker.begin() as session:
        application = Application(
            sent_at=date(2026, 10, 2),
            method="electronique",
            company="Exemple SA",
            job_title="Ingénieur DevOps",
            orp_month="2026-10",
            status="entretien",
            interview_at=datetime(2026, 10, 6, 9, 0, tzinfo=UTC),
            **extra,
        )
        session.add(application)
        await session.flush()
        return application.id


async def reset(runtime: Runtime) -> None:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE applications, interviews, notifications CASCADE"))


async def test_feedback_crud_and_listing(client: AsyncClient, runtime: Runtime) -> None:
    await reset(runtime)
    app_id = await add_application(runtime)
    body = {
        "kind": "technique",
        "held_at": "2026-10-06",
        "format": "visio",
        "interviewers": ["manager", "equipe"],
        "rating": 4,
        "stress": 3,
        "questions": [
            {"text": "Pourquoi ce poste ?"},
            {"text": "Kubernetes en production", "difficult": True},
        ],
        "salary_asked": True,
        "salary_answer": "  95 000 CHF  ",
        "to_prepare": ["Exemple de migration", "  "],
        "next_step": "reponse",
        "next_step_at": "2026-10-20",
        "thanks": "todo",
    }
    created = await client.post(f"/api/applications/{app_id}/interviews", json=body)
    assert created.status_code == 201
    interview = created.json()
    assert interview["salary_answer"] == "95 000 CHF" and interview["to_prepare"] == [
        "Exemple de migration"
    ]
    assert interview["questions"][1] == {"text": "Kubernetes en production", "difficult": True}
    # Le ressenti global est obligatoire, le reste facultatif.
    assert (await client.post(f"/api/applications/{app_id}/interviews", json={})).status_code == 422
    assert (
        await client.post("/api/applications/999999/interviews", json={"rating": 3})
    ).status_code == 404

    listed = (await client.get("/api/applications")).json()
    assert [i["kind"] for i in listed[0]["interviews"]] == ["technique"]
    updated = await client.put(
        f"/api/interviews/{interview['id']}",
        json={**body, "rating": 5, "went_well": "Démo réussie"},
    )
    assert updated.json()["rating"] == 5 and updated.json()["went_well"] == "Démo réussie"
    assert (await client.delete(f"/api/interviews/{interview['id']}")).status_code == 204
    assert (await client.get(f"/api/applications/{app_id}/interviews")).json() == []
    await reset(runtime)


async def test_reminder_the_day_after(runtime: Runtime, client: AsyncClient) -> None:
    # ntfy n'est pas configuré dans les tests : l'alerte ne va que dans la cloche.
    await reset(runtime)
    app_id = await add_application(runtime)
    # Le jour même : rien ; le lendemain : une alerte, une seule fois.
    assert await notify_interviews(runtime, date(2026, 10, 6)) == 0
    assert await notify_interviews(runtime, date(2026, 10, 7)) == 1
    assert await notify_interviews(runtime, date(2026, 10, 8)) == 0
    async with runtime.sessionmaker() as session:
        alert = await session.scalar(select(Notification).where(Notification.kind == "interview"))
    assert alert is not None and alert.link == "/candidatures/suivi?mois=2026-10&jour=2026-10-06"
    assert "Exemple SA" in alert.title

    today = (await client.get("/api/today")).json()
    # Aujourd'hui (date réelle) : l'entretien du 6 octobre est rappelé pendant 14 jours.
    pending = today["interviews_to_review"]
    assert all(p["application_id"] == app_id for p in pending)
    # Retour fait : plus rien à rappeler.
    await client.post(
        f"/api/applications/{app_id}/interviews", json={"rating": 3, "held_at": "2026-10-06"}
    )
    assert (await client.get("/api/today")).json()["interviews_to_review"] == []
    await reset(runtime)
