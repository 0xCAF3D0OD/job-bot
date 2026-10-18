"""S'entraîner à l'entretien (docs/75), avec une IA simulée : aucun appel réseau."""

import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from jobbot.db.models import Application, Contact, Interview
from jobbot.interviews import practice
from jobbot.llm import common
from jobbot.llm.client import RawResult, Refused
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring

from .conftest import admin_engine


async def reset(runtime: Runtime) -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("TRUNCATE applications, interviews, interview_practices, contacts CASCADE")
        )
        await conn.execute(text("DELETE FROM llm_calls WHERE purpose = 'practice'"))
        await conn.execute(
            text(
                "DELETE FROM settings WHERE key IN "
                "('interview_prepared', 'interview_to_prepare_extra')"
            )
        )


async def add_application(runtime: Runtime) -> int:
    async with runtime.sessionmaker.begin() as session:
        application = Application(
            sent_at=date(2026, 10, 2),
            method="electronique",
            company="Exemple SA",
            job_title="Ingénieur DevOps",
            orp_month="2026-10",
            status="entretien",
        )
        session.add(application)
        await session.flush()
        session.add(
            Interview(
                application_id=application.id,
                kind="technique",
                rating=2,
                interviewers=["rh"],
                questions=[{"text": "Expliquez un déploiement canary", "difficult": True}],
                to_prepare=["Exemple chiffré"],
            )
        )
        session.add(
            Contact(
                application_id=application.id,
                name="Alex Recruteur",
                role="recruiter",
                channel="email",
                contacted_on=date(2026, 10, 3),
            )
        )
        return application.id


class Fake:
    """Le recruteur suit un scénario ; le retour est toujours le même."""

    def __init__(self, script: list[dict[str, str]]) -> None:
        self.script = script
        self.calls: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.calls.append(params)
        body: dict[str, Any]
        if params["system"][0]["text"] == practice.FEEDBACK:
            body = {
                "questions": [
                    {
                        "question": 1,
                        "level": "a_preciser",
                        "good": "Clair",
                        "missing": "Un chiffre",
                        "better": "J'ai migré…",
                    },
                    {"question": 9, "level": "solide", "good": "", "missing": "", "better": ""},
                    {
                        "question": 3,
                        "level": "inconnu",
                        "good": "",
                        "missing": "Un exemple",
                        "better": "…",
                    },
                ],
                "strengths": ["Structure", "Calme", "Vocabulaire"],
                "work_on": ["Préparer un exemple chiffré", "Parler de Kubernetes", "Conclure"],
            }
        elif not self.script:
            raise Refused
        else:
            body = self.script.pop(0)
        payload = f"<reponse>{json.dumps(body, ensure_ascii=False)}</reponse>"
        return RawResult(payload, practice.MODEL, Usage(3000, 0, 0, 200), "end_turn")


def question(n: int) -> dict[str, str]:
    return {"action": "question", "text": f"Question {n} ?"}


@pytest.fixture
def ai(monkeypatch: pytest.MonkeyPatch, runtime: Runtime) -> Any:
    def install(script: list[dict[str, str]]) -> Fake:
        fake = Fake(script)
        monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
        monkeypatch.setattr(type(runtime.settings), "llm_configured", property(lambda _self: True))
        return fake

    return install


async def test_full_practice_then_feedback(client: AsyncClient, runtime: Runtime, ai: Any) -> None:
    await reset(runtime)
    app_id = await add_application(runtime)
    fake = ai(
        [
            question(1),
            {"action": "relance", "text": "Un exemple concret ?"},
            # Une seule relance par question : la seconde devient la question suivante.
            {"action": "relance", "text": "Question 2 ?"},
            question(3),
            question(4),
            question(5),
            # Après la cinquième, une « question » de plus vaut fin.
            question(6),
        ]
    )
    defaults = (
        await client.get(f"/api/interview-practices/defaults?application_id={app_id}")
    ).json()
    assert defaults["kind"] == "technique" and defaults["can_practice"] is True
    started = await client.post(
        "/api/interview-practices",
        json={"application_id": app_id, "kind": "technique", "tone": "exigeant", "language": "en"},
    )
    assert started.status_code == 201
    body = started.json()
    practice_id = body["id"]
    assert (body["question"], body["turns"][0]["text"], body["company"]) == (
        1,
        "Question 1 ?",
        "Exemple SA",
    )

    body = (
        await client.post(f"/api/interview-practices/{practice_id}/answer", json={"text": "Bof"})
    ).json()
    assert body["turns"][-1] == {
        "role": "recruteur",
        "text": "Un exemple concret ?",
        "question": 1,
        "relance": True,
        "skipped": False,
    }
    body = (
        await client.post(f"/api/interview-practices/{practice_id}/answer", json={"text": "Voilà"})
    ).json()
    assert (body["question"], body["turns"][-1]["relance"]) == (2, False)
    # Passer la question : pas de relance permise ensuite.
    body = (await client.post(f"/api/interview-practices/{practice_id}/skip")).json()
    assert body["question"] == 3
    assert "pas de relance" in fake.calls[-1]["messages"][0]["content"]
    for _ in range(2):
        await client.post(f"/api/interview-practices/{practice_id}/answer", json={"text": "Oui"})
    body = (
        await client.post(f"/api/interview-practices/{practice_id}/answer", json={"text": "Fin"})
    ).json()
    assert body["status"] == "termine" and body["question"] == 5
    feedback = body["feedback"]
    # Seules les questions répondues ; un repère inconnu devient « à préciser ».
    assert [(q["question"], q["level"]) for q in feedback["questions"]] == [
        (1, "a_preciser"),
        (3, "a_preciser"),
    ]
    assert feedback["work_on"][0] == "Préparer un exemple chiffré"
    assert body["cost_chf"] > 0
    assert (
        await client.post(f"/api/interview-practices/{practice_id}/answer", json={"text": "Encore"})
    ).status_code == 409

    # Rien de personnel n'est envoyé : ni contacts, ni recruteurs notés.
    sent = json.dumps(
        [c["system"] for c in fake.calls] + [c["messages"] for c in fake.calls], ensure_ascii=False
    )
    assert "Alex Recruteur" not in sent
    assert "Expliquez un déploiement canary" in sent and "Exemple SA" in sent
    assert "langue : anglais" in sent and "ton : exigeant" in sent
    # Le contexte est mis en cache.
    assert fake.calls[0]["system"][-1]["cache_control"] == {"type": "ephemeral"}

    # Un entraînement n'est pas un vrai entretien.
    insights = (await client.get("/api/interviews/insights")).json()
    assert insights["count"] == 1
    added = await client.post(
        "/api/interviews/insights/to-prepare",
        json={"text": "Préparer un exemple chiffré", "done": False},
    )
    assert [p["text"] for p in added.json()["to_prepare"]] == [
        "Exemple chiffré",
        "Préparer un exemple chiffré",
    ]
    listed = (await client.get(f"/api/interview-practices?application_id={app_id}")).json()
    assert [p["id"] for p in listed] == [practice_id]
    assert (await client.delete(f"/api/interview-practices/{practice_id}")).status_code == 204
    assert (await client.get(f"/api/interview-practices/{practice_id}")).status_code == 404
    await reset(runtime)


async def test_finish_early_retry_and_budget(
    client: AsyncClient, runtime: Runtime, ai: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    await reset(runtime)
    fake = ai([question(1)])
    # Sans candidature : un entretien type.
    body = (await client.post("/api/interview-practices", json={})).json()
    practice_id = body["id"]
    assert body["company"] is None and body["kind"] == "rh"
    assert "Entretien type" in fake.calls[0]["system"][-1]["text"]
    # Pas de retour sans au moins une réponse.
    assert (await client.post(f"/api/interview-practices/{practice_id}/finish")).status_code == 409

    # L'IA échoue après la réponse : « Réessayer » relance le recruteur.
    fake.script = []
    failed = await client.post(
        f"/api/interview-practices/{practice_id}/answer", json={"text": "Bonjour"}
    )
    assert failed.status_code == 409
    body = (await client.get(f"/api/interview-practices/{practice_id}")).json()
    assert body["waiting"] is True
    fake.script = [question(2)]
    body = (await client.post(f"/api/interview-practices/{practice_id}/retry")).json()
    assert (body["waiting"], body["question"]) == (False, 2)
    body = (await client.post(f"/api/interview-practices/{practice_id}/finish")).json()
    assert body["status"] == "termine"

    # Plafond : refusé avant de commencer, s'il ne reste pas de quoi aller jusqu'au retour.
    async def low_budget(*_args: Any) -> tuple[Decimal, Decimal, Decimal]:
        return Decimal("0.9"), Decimal("1"), Decimal("0.8")

    monkeypatch.setattr(common, "budget_state", low_budget)
    refused = await client.post("/api/interview-practices", json={})
    assert refused.status_code == 409 and "plafond" in refused.json()["detail"]
    await reset(runtime)


def test_guess_language() -> None:
    assert (
        practice.guess_language("We are looking for an engineer to join our team and you will")
        == "en"
    )
    assert (
        practice.guess_language("Wir suchen für unser Team eine Ingenieurin und Sie bei der")
        == "de"
    )
    assert practice.guess_language("Nous cherchons pour notre équipe un ingénieur et vous") == "fr"
    assert practice.guess_language(None) == "fr"


async def test_two_answers_at_once_keep_one(client: AsyncClient, runtime: Runtime, ai: Any) -> None:
    """Deux envois simultanés : un seul passe, une seule question suit (docs/76 §1)."""
    import asyncio

    await reset(runtime)
    fake = ai([question(1), question(2), question(3)])
    practice_id = (await client.post("/api/interview-practices", json={})).json()["id"]
    url = f"/api/interview-practices/{practice_id}/answer"
    first, second = await asyncio.gather(
        client.post(url, json={"text": "Une"}), client.post(url, json={"text": "Deux"})
    )
    assert sorted([first.status_code, second.status_code]) == [200, 409]
    body = (await client.get(f"/api/interview-practices/{practice_id}")).json()
    assert [t["role"] for t in body["turns"]] == ["recruteur", "candidat", "recruteur"]
    assert len(fake.calls) == 2
    await reset(runtime)


def test_unreadable_answers() -> None:
    """Réponses de l'IA sans balise, en JSON faux, ou en liste : rien n'est inventé."""
    for raw in ("Bonjour", "<reponse>{faux}</reponse>", '<reponse>["a"]</reponse>'):
        assert practice.parse_turn(raw) is None
        assert practice.parse_feedback(raw, {1}) is None
    long_point = "x" * 500
    parsed = practice.parse_feedback(
        f'<reponse>{{"questions": [], "strengths": [], "work_on": ["{long_point}"]}}</reponse>',
        set(),
    )
    assert parsed is not None and len(parsed["work_on"][0]) == practice.POINT_MAX


async def test_edges(client: AsyncClient, runtime: Runtime, ai: Any) -> None:
    await reset(runtime)
    # Candidature inconnue (ou d'un autre compte) : 404.
    ai([question(1)])
    assert (
        await client.post("/api/interview-practices", json={"application_id": 999_999})
    ).status_code == 404
    # Pas de première question : l'entraînement n'est pas gardé.
    ai([])
    assert (await client.post("/api/interview-practices", json={})).status_code == 409
    assert (await client.get("/api/interview-practices")).json() == []

    fake = ai([question(1)])
    practice_id = (await client.post("/api/interview-practices", json={})).json()["id"]
    # « Réessayer » alors que le recruteur a déjà parlé : rien ne se passe, rien n'est payé.
    calls = len(fake.calls)
    body = (await client.post(f"/api/interview-practices/{practice_id}/retry")).json()
    assert len(body["turns"]) == 1 and len(fake.calls) == calls
    # Une réponse faite d'espaces est refusée comme une réponse vide.
    blank = await client.post(f"/api/interview-practices/{practice_id}/answer", json={"text": "  "})
    assert blank.status_code == 422
    fake.script = [question(2)]
    await client.post(f"/api/interview-practices/{practice_id}/answer", json={"text": "Oui"})
    done = (await client.post(f"/api/interview-practices/{practice_id}/finish")).json()
    assert done["status"] == "termine"
    # « Terminer » une seconde fois : rien de plus.
    calls = len(fake.calls)
    again = await client.post(f"/api/interview-practices/{practice_id}/finish")
    assert again.status_code == 200 and len(fake.calls) == calls
    # « Ajouter à À préparer » : un texte seul, 200 caractères au plus.
    assert (
        await client.post("/api/interviews/insights/to-prepare", json={"text": "Un point"})
    ).status_code == 200
    assert (
        await client.post("/api/interviews/insights/to-prepare", json={"text": "x" * 201})
    ).status_code == 422
    await reset(runtime)


async def test_retry_after_last_question_asks_feedback(
    client: AsyncClient, runtime: Runtime, ai: Any
) -> None:
    """Le retour a échoué après la dernière réponse : « Réessayer » le redemande, sans relancer
    le recruteur (docs/76 §3)."""
    await reset(runtime)
    fake = ai([question(n) for n in range(1, 6)])
    practice_id = (await client.post("/api/interview-practices", json={})).json()["id"]
    url = f"/api/interview-practices/{practice_id}"
    for _ in range(4):
        await client.post(f"{url}/skip")
    # Le recruteur n'a plus de réplique : la dernière réponse attend le retour.
    original = Fake.score

    async def broken(params: dict[str, Any]) -> RawResult:
        if params["system"][0]["text"] == practice.FEEDBACK:
            raise Refused
        result: RawResult = await original(fake, params)
        return result

    fake.score = broken
    failed = await client.post(f"{url}/answer", json={"text": "Ma dernière réponse"})
    assert failed.status_code == 409
    assert (await client.get(url)).json()["waiting"] is True
    del fake.score
    calls = len(fake.calls)
    body = (await client.post(f"{url}/retry")).json()
    assert body["status"] == "termine"
    # Un seul appel, celui du retour.
    assert len(fake.calls) == calls + 1
    assert fake.calls[-1]["system"][0]["text"] == practice.FEEDBACK
    await reset(runtime)
