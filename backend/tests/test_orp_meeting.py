"""Le rendez-vous ORP (docs/83) : la feuille préparée à partir de tes données, sans IA."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import (
    Application,
    Evaluation,
    Offer,
    OfferLink,
    OrpMeeting,
    Setting,
    Training,
    TrainingMark,
)
from jobbot.orp import meeting
from jobbot.profiles.service import main_profile
from jobbot.runtime import Runtime

from .conftest import admin_engine

NOW = datetime.now(UTC)
TODAY = NOW.astimezone(LOCAL_TZ).date()
RESET = (
    "TRUNCATE applications, offers, orp_meetings, orp_months, training_marks CASCADE",
    "DELETE FROM trainings WHERE url LIKE 'https://rdv.example/%'",
    "DELETE FROM settings WHERE key = 'orp_monthly_target'",
)


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with admin_engine().begin() as conn:
        for statement in RESET:
            await conn.execute(text(statement))
    yield runtime
    async with admin_engine().begin() as conn:
        for statement in RESET:
            await conn.execute(text(statement))


async def _situation(rt: Runtime) -> int:
    """Douze candidatures jobup sans réponse, des offres bien notées qui demandent Terraform,
    une formation payante envisagée, une assignation de l'ORP. Rend l'id de la formation."""
    async with rt.sessionmaker.begin() as session:
        session.add(Setting(key="orp_monthly_target", value=12))
        for n in range(12):
            offer = Offer(
                fingerprint=f"rdv{n}",
                title=f"Poste {n}",
                company=f"Entreprise {n} SA",
                first_seen_at=NOW - timedelta(days=20),
                last_seen_at=NOW,
            )
            session.add(offer)
            await session.flush()
            session.add(OfferLink(offer_id=offer.id, source="jobup", url=f"https://j.example/{n}"))
            session.add(
                Evaluation(
                    offer_id=offer.id,
                    filter_passed=True,
                    criteria_hash="h",
                    score=75,
                    keywords_asks=[
                        {"text": "Terraform", "covered": False},
                        {"text": "Kubernetes", "covered": True},
                    ]
                    if n < 8
                    else [],
                )
            )
            session.add(
                Application(
                    offer_id=offer.id,
                    sent_at=TODAY - timedelta(days=n + 3),
                    method="electronique",
                    company=f"Entreprise {n} SA",
                    job_title=f"Poste {n}",
                    orp_month=(TODAY - timedelta(days=n + 3)).strftime("%Y-%m"),
                    assigned_by_orp=n == 0,
                )
            )
        training = Training(
            title="Terraform Associate",
            provider="HashiCorp",
            kind="certification",
            format="exam_online",
            language="en",
            price="paid",
            url="https://rdv.example/terraform",
            origin="catalog",
        )
        session.add(training)
        await session.flush()
        profile = await main_profile(session)
        session.add(
            TrainingMark(profile_id=profile.id, training_id=training.id, status="interested")
        )
        return training.id


async def test_the_sheet_comes_from_your_data(rt: Runtime) -> None:
    training_id = await _situation(rt)
    async with rt.sessionmaker() as session:
        prep = await meeting.prepare(session)
    assert len(prep.summaries) == 2
    assert "Aucune réponse en 3 mois, sur 12 candidatures." in prep.blockers
    # « Ce qui te manque » : 8 offres bien notées sur 12, et la formation qui le couvre.
    assert prep.offers == 12
    assert [(m.skill, m.count, m.training_id) for m in prep.missing] == [
        ("Terraform", 8, training_id)
    ]
    keys = {q.key: q.checked for q in prep.questions}
    assert keys[f"funding:{training_id}"] is True
    assert keys["measure"] is True
    assert any(k.startswith("assignment:") for k in keys)
    assert keys["intermediate"] is False
    texts = [o.text for o in prep.obligations]
    assert any(t.startswith("Preuves de ") for t in texts)
    assert any(t.startswith("Assignation chez Entreprise 0 SA") for t in texts)


async def test_meeting_questions_and_sheet(client: AsyncClient, rt: Runtime) -> None:
    await _situation(rt)
    page = (await client.get("/api/orp-meeting")).json()
    assert page["meeting"] is None
    refused = await client.put("/api/orp-meeting/questions", json={"questions": []})
    assert refused.status_code == 409
    starts = datetime.combine(TODAY + timedelta(days=1), datetime.min.time(), LOCAL_TZ).replace(
        hour=9, minute=30
    )
    saved = await client.put(
        "/api/orp-meeting",
        json={"starts_at": starts.isoformat(), "place": " ORP de Lausanne ", "advisor": ""},
    )
    assert saved.json()["meeting"]["place"] == "ORP de Lausanne"
    assert saved.json()["meeting"]["advisor"] is None
    questions = saved.json()["preparation"]["questions"]
    for question in questions:
        question["checked"] = question["key"] == "intermediate"
    questions.append({"key": "custom:1", "text": "Puis-je travailler à 80 % ?", "checked": True})
    page = (await client.put("/api/orp-meeting/questions", json={"questions": questions})).json()
    checked = [q["text"] for q in page["preparation"]["questions"] if q["checked"]]
    assert checked == [
        "Si je prends un emploi temporaire, comment déclarer un gain intermédiaire ?",
        "Puis-je travailler à 80 % ?",
    ]
    assert any(o["text"].startswith("Rendez-vous le ") for o in page["preparation"]["obligations"])
    # Demain : la page Aujourd'hui le rappelle.
    today = (await client.get("/api/today")).json()
    assert today["orp_meeting_at"] is not None
    sheet = await client.get("/api/orp-meeting/feuille.pdf", params={"name": "Camille Exemple"})
    assert sheet.status_code == 200 and sheet.content.startswith(b"%PDF")
    assert sheet.headers["content-disposition"].startswith("attachment")
    # Le rendez-vous passé n'est plus « le prochain ».
    async with rt.sessionmaker.begin() as session:
        await session.execute(
            text("update orp_meetings set starts_at = :past"), {"past": NOW - timedelta(days=3)}
        )
    assert (await client.get("/api/orp-meeting")).json()["meeting"] is None
    assert (await client.get("/api/today")).json()["orp_meeting_at"] is None
    assert (await client.delete("/api/orp-meeting")).status_code == 200


async def test_without_data_the_sheet_stays_honest(rt: Runtime) -> None:
    """Peu de données, pas de conclusion : ni blocage ni manque inventés."""
    async with rt.sessionmaker() as session:
        prep = await meeting.prepare(session)
    assert prep.blockers == [] and prep.missing == [] and prep.works is None
    assert [q.key for q in prep.questions] == ["intermediate"]
    assert not any(isinstance(o.due, date) and o.done for o in prep.obligations[1:])


def test_your_choices_survive_new_suggestions() -> None:
    suggested = [
        meeting.Question("measure", "Une mesure ?", True),
        meeting.Question("intermediate", "Gain ?"),
    ]
    saved = [
        {"key": "measure", "checked": False},
        {"key": "custom:2", "text": "Ma question", "checked": True},
        {"key": "custom:3", "text": "  ", "checked": True},
    ]
    merged = meeting.merge(suggested, saved)
    assert [(q.key, q.checked) for q in merged] == [
        ("measure", False),
        ("intermediate", False),
        ("custom:2", True),
    ]
    assert OrpMeeting.__tablename__ == "orp_meetings"
