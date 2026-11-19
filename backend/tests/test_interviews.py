"""Retour d'entretien (docs/23) : formulaire, liste avec la candidature, rappel du lendemain."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from jobbot.db.models import Application, Notification
from jobbot.notify.interviews import LOCAL_TZ, notify_interviews
from jobbot.runtime import Runtime

from .conftest import admin_engine


async def add_application(runtime: Runtime, **extra: object) -> int:
    async with runtime.sessionmaker.begin() as session:
        values: dict[str, object] = {
            "company": "Exemple SA",
            "interview_at": datetime(2026, 10, 6, 9, 0, tzinfo=UTC),
            **extra,
        }
        application = Application(
            sent_at=date(2026, 10, 2),
            method="electronique",
            job_title="Ingénieur DevOps",
            orp_month="2026-10",
            status="entretien",
            **values,
        )
        session.add(application)
        await session.flush()
        return application.id


async def reset(runtime: Runtime) -> None:
    async with admin_engine().begin() as conn:
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
    assert alert is not None and alert.link == f"/candidatures/suivi?candidature={app_id}&retour=1"
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


async def test_insights_prepared_and_coach(
    client: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    from jobbot.interviews import service
    from jobbot.llm.client import RawResult
    from jobbot.llm.pricing import Usage
    from jobbot.scoring import service as scoring

    await reset(runtime)
    first = await add_application(runtime)
    second = await add_application(runtime, company="Autre SA")
    await client.post(
        f"/api/applications/{first}/interviews",
        json={
            "rating": 2,
            "questions": [
                {"text": "Vos points faibles ?", "difficult": True},
                {"text": "Présentez-vous"},
            ],
            "went_badly": "Réponse floue sur Kubernetes",
            "to_prepare": ["Exemple chiffré de projet"],
        },
    )
    await client.post(
        f"/api/applications/{second}/interviews",
        json={"rating": 4, "questions": [{"text": "présentez-vous"}], "went_well": "Bonne démo"},
    )
    insights = (await client.get("/api/interviews/insights")).json()
    assert insights["count"] == 2 and insights["average_rating"] == 3.0
    assert [(q["text"], q["count"], q["difficult"]) for q in insights["questions"]] == [
        ("Vos points faibles ?", 1, 1),
        ("Présentez-vous", 2, 0),
    ]
    assert insights["went_well"][0]["company"] == "Autre SA"
    assert insights["to_prepare"] == [{"text": "Exemple chiffré de projet", "done": False}]
    checked = await client.put(
        "/api/interviews/insights/prepared",
        json={"text": "exemple chiffré de projet", "done": True},
    )
    assert checked.json()["to_prepare"][0]["done"] is True

    # Conseils de l'IA : sans clé, refusé ; avec une réponse simulée, gardés.
    assert (await client.post("/api/interviews/coach", json={})).status_code == 409
    calls: list[dict[str, Any]] = []

    class Fake:
        async def score(self, params: dict[str, Any]) -> RawResult:
            calls.append(params)
            text_ = (
                '<reponse>{"pistes": ["Prépare un exemple chiffré"], '
                '"answers": [{"question": "Vos points faibles ?", "answer": "Je…"}], '
                '"questions_to_ask": ["Quelle équipe ?"]}</reponse>'
            )
            return RawResult(text_, service.MODEL, Usage(4000, 0, 0, 800), "end_turn")

    monkeypatch.setattr(scoring, "make_client", lambda _settings: Fake())
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
    coached = await client.post("/api/interviews/coach", json={"application_id": first})
    assert coached.status_code == 200
    coaching = coached.json()["coaching"]
    assert (
        coaching["pistes"] == ["Prépare un exemple chiffré"] and coaching["application_id"] == first
    )
    content = calls[0]["messages"][0]["content"]
    assert "Vos points faibles ?" in content and "<prochain>" in content
    assert "Exemple SA" in content  # le prochain entretien nomme l'entreprise, pas toi
    await reset(runtime)
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM settings WHERE key IN ('interview_prepared', 'interview_coaching')")
        )


async def test_coach_counts_an_unreadable_answer(
    client: AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Une réponse illisible coûte quand même : son appel reste compté (docs/76 §5)."""
    from jobbot.interviews import service
    from jobbot.llm.client import RawResult
    from jobbot.llm.pricing import Usage
    from jobbot.scoring import service as scoring

    await reset(runtime)
    app_id = await add_application(runtime)
    await client.post(f"/api/applications/{app_id}/interviews", json={"rating": 3})

    class Fake:
        async def score(self, params: dict[str, Any]) -> RawResult:
            return RawResult("pas de balise", service.MODEL, Usage(4000, 0, 0, 800), "end_turn")

    monkeypatch.setattr(scoring, "make_client", lambda _settings: Fake())
    monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
    async with runtime.engine.begin() as conn:
        await conn.execute(text("DELETE FROM llm_calls WHERE purpose = 'coach'"))
    refused = await client.post("/api/interviews/coach", json={})
    assert refused.status_code == 409 and "illisible" in refused.json()["detail"]
    async with runtime.engine.begin() as conn:
        counted = await conn.scalar(text("SELECT count(*) FROM llm_calls WHERE purpose = 'coach'"))
    assert counted == 1
    async with runtime.engine.begin() as conn:
        await conn.execute(text("DELETE FROM llm_calls WHERE purpose = 'coach'"))
    await reset(runtime)


async def test_debrief_page(client: AsyncClient, runtime: Runtime) -> None:
    """« Faire le point » (planche FairePoint, Kevin 18.11.2026) : le ressenti en trois mots, la
    suite et les notes ; la relance est calculée (jour de l'entretien + 7 jours), jamais saisie."""
    await reset(runtime)
    app_id = await add_application(runtime, interview_at=datetime(2026, 11, 12, 13, 0, tzinfo=UTC))
    empty = (await client.get(f"/api/applications/{app_id}/debrief")).json()
    assert empty["company"] == "Exemple SA" and empty["feeling"] is None
    assert empty["follow_up_on"] == "2026-11-19"
    body = {"feeling": "bien", "next_step": "reponse", "notes": "  Équipe de 6.  "}
    saved = (await client.put(f"/api/applications/{app_id}/debrief", json=body)).json()
    assert (saved["feeling"], saved["notes"]) == ("bien", "Équipe de 6.")
    [interview] = (await client.get(f"/api/applications/{app_id}/interviews")).json()
    # Le jour en Suisse ; la relance va dans la suite, pour l'agenda ; pas de note sur 5 inventée.
    assert interview["held_at"] == "2026-11-12" and interview["next_step_at"] == "2026-11-19"
    assert interview["rating"] is None and interview["feeling"] == "bien"
    # Le point refait complète le même retour ; « On m'a dit non » n'a pas de relance.
    again = {"feeling": "pas_bien", "next_step": "refus"}
    await client.put(f"/api/applications/{app_id}/debrief", json=again)
    [interview] = (await client.get(f"/api/applications/{app_id}/interviews")).json()
    assert (interview["feeling"], interview["next_step"], interview["next_step_at"]) == (
        "pas_bien",
        "refus",
        None,
    )
    assert interview["notes"] is None
    # Le formulaire complet peut rouvrir ce retour sans note sur 5, et la garder vide.
    kept = await client.put(f"/api/interviews/{interview['id']}", json={"kind": "technique"})
    assert kept.status_code == 200 and kept.json()["feeling"] == "pas_bien"
    # Le ressenti est obligatoire ; une candidature sans entretien n'a pas de point.
    assert (await client.put(f"/api/applications/{app_id}/debrief", json={})).status_code == 422
    no_meeting = await add_application(runtime, interview_at=None)
    assert (await client.get(f"/api/applications/{no_meeting}/debrief")).status_code == 404
    assert (await client.get("/api/applications/999999/debrief")).status_code == 404


async def test_debrief_keeps_the_full_form(client: AsyncClient, runtime: Runtime) -> None:
    """Un retour déjà fait par le formulaire complet garde sa note et ses réponses."""
    await reset(runtime)
    app_id = await add_application(runtime)
    await client.post(
        f"/api/applications/{app_id}/interviews",
        json={"held_at": "2026-10-06", "rating": 4, "went_well": "Démo"},
    )
    await client.put(f"/api/applications/{app_id}/debrief", json={"feeling": "moyen"})
    [interview] = (await client.get(f"/api/applications/{app_id}/interviews")).json()
    assert (interview["rating"], interview["went_well"], interview["feeling"]) == (
        4,
        "Démo",
        "moyen",
    )
    # La moyenne des notes ignore les points sans note.
    insights = (await client.get("/api/interviews/insights")).json()
    assert insights["average_rating"] == 4


async def test_interview_debrief_reopens_a_past_point(
    client: AsyncClient, runtime: Runtime
) -> None:
    """« Voir le retour » sur ordinateur (accord de Kevin du 19.11.2026) : le panneau de Rendez-vous
    rouvre le point d'un retour précis, même après un autre entretien, et le met à jour sans toucher
    au reste du retour."""
    await reset(runtime)
    app_id = await add_application(runtime, interview_at=datetime(2026, 11, 12, 13, 0, tzinfo=UTC))
    first = (
        await client.post(
            f"/api/applications/{app_id}/interviews",
            json={"held_at": "2026-10-06", "rating": 4, "went_well": "Démo"},
        )
    ).json()
    opened = (await client.get(f"/api/interviews/{first['id']}/debrief")).json()
    # Pas l'entretien prévu ce jour-là : la date du retour, sans heure inventée.
    assert opened["interview_at"].startswith("2026-10-06T00:00:00")
    assert opened["follow_up_on"] == "2026-10-13" and opened["feeling"] is None
    body = {"feeling": "moyen", "next_step": "reponse", "notes": "Relancer Anna"}
    saved = (await client.put(f"/api/interviews/{first['id']}/debrief", json=body)).json()
    assert (saved["feeling"], saved["notes"]) == ("moyen", "Relancer Anna")
    interviews = (await client.get(f"/api/applications/{app_id}/interviews")).json()
    [kept] = [i for i in interviews if i["id"] == first["id"]]
    assert (kept["rating"], kept["went_well"], kept["next_step_at"]) == (4, "Démo", "2026-10-13")
    # Le point de l'entretien prévu reste un autre retour.
    assert len(interviews) == 1
    planned = (await client.get(f"/api/applications/{app_id}/debrief")).json()
    assert planned["feeling"] is None and planned["interview_at"].startswith("2026-11-12T13:00")
    assert (await client.get("/api/interviews/999999/debrief")).status_code == 404
    assert (await client.put(f"/api/interviews/{first['id']}/debrief", json={})).status_code == 422


async def test_two_interviews_stay_separate(runtime: Runtime, client: AsyncClient) -> None:
    """« Ajouter un entretien » (§72p, Kevin 19.11) : le 2e ne retire jamais le 1er de « À noter »,
    qui en sort seulement quand son point est fait."""
    await reset(runtime)
    app_id = await add_application(runtime)
    first = datetime.now(UTC) - timedelta(days=3)
    async with runtime.sessionmaker.begin() as session:
        application = await session.get(Application, app_id)
        assert application is not None
        application.interview_at = first
        application.interview_place = "Genève"
    second = {"round": "2", "at": "2099-12-01T13:00:00Z", "place": " Alpstack, Lausanne "}
    added = await client.post(f"/api/applications/{app_id}/interview-plan", json=second)
    assert added.status_code == 204

    listed = (await client.get("/api/applications")).json()[0]
    assert listed["interview_at"].startswith("2099-12-01")
    assert listed["interview_place"] == "Alpstack, Lausanne"
    assert listed["interview_round"] == "2"
    assert listed["status"] == "entretien"
    # Le 1er reste un élément à part, pas un retour : à noter jusqu'à son point.
    assert listed["interviews"] == []
    [planned] = listed["planned"]
    assert planned["place"] == "Genève" and planned["round"] is None
    pending = (await client.get("/api/today")).json()["interviews_to_review"]
    assert [p["link"] for p in pending] == [
        f"/candidatures/rendez-vous-orp?rdv=point-r{planned['id']}"
    ]

    # Son point : le même entretien devient un retour, daté du jour prévu, et sort de « À noter ».
    debrief = (await client.get(f"/api/interviews/{planned['id']}/debrief")).json()
    # L'heure prévue est connue : la carte du haut la montre.
    assert abs(datetime.fromisoformat(debrief["interview_at"]) - first) < timedelta(seconds=1)
    saved = await client.put(f"/api/interviews/{planned['id']}/debrief", json={"feeling": "moyen"})
    assert saved.status_code == 200
    listed = (await client.get("/api/applications")).json()[0]
    assert listed["planned"] == []
    [review] = listed["interviews"]
    assert review["held_at"] == first.astimezone(LOCAL_TZ).date().isoformat()
    assert review["feeling"] == "moyen"
    assert (await client.get("/api/today")).json()["interviews_to_review"] == []

    # Un 3e alors que le point du 2e est fait : rien n'est gardé deux fois.
    async with runtime.sessionmaker.begin() as session:
        application = await session.get(Application, app_id)
        assert application is not None
        application.interview_at = datetime.now(UTC) - timedelta(days=1)
    day = (datetime.now(UTC) - timedelta(days=1)).astimezone(LOCAL_TZ).date()
    assert (
        await client.put(f"/api/applications/{app_id}/debrief", json={"feeling": "bien"})
    ).status_code == 200
    third = {"round": "final", "at": "2099-12-10T09:00:00Z"}
    assert (
        await client.post(f"/api/applications/{app_id}/interview-plan", json=third)
    ).status_code == 204
    listed = (await client.get("/api/applications")).json()[0]
    assert listed["planned"] == []
    assert [i["held_at"] for i in listed["interviews"]][-1] == day.isoformat()
    assert listed["interview_place"] is None and listed["interview_round"] == "final"
    await reset(runtime)
