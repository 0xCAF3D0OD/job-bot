"""Bilan de ta recherche (docs/42) : parcours, comparaisons, phrase de tête, résumé ORP."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.db.models import Application, Contact, Evaluation, Offer, OfferLink
from jobbot.insights.service import Comparison, Group, headline
from jobbot.runtime import Runtime
from jobbot.settings import Settings

TRUNCATE = "TRUNCATE offers, applications, contacts CASCADE"


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text(TRUNCATE))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with runtime.engine.begin() as conn:
        await conn.execute(text(TRUNCATE))


SENT = date.today() - timedelta(days=20)
MONTH = f"{date.today():%Y-%m}"


async def add(
    runtime: Runtime,
    company: str,
    *,
    source: str | None = None,
    score: int | None = None,
    spontaneous: bool = False,
    **values: Any,
) -> int:
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        offer_id = None
        if source is not None or spontaneous:
            offer = Offer(
                fingerprint=company,
                title="DevOps Engineer",
                company=company,
                status="applied",
                first_seen_at=now - timedelta(days=21),
                last_seen_at=now,
                spontaneous=spontaneous,
            )
            session.add(offer)
            await session.flush()
            offer_id = offer.id
            if source is not None:
                session.add(OfferLink(offer_id=offer.id, source=source, url=f"https://{company}"))
                session.add(
                    Evaluation(
                        offer_id=offer.id,
                        filter_passed=score is not None,
                        criteria_hash="x",
                        score=score,
                    )
                )
        application = Application(
            offer_id=offer_id,
            sent_at=SENT,
            method="electronique",
            company=company,
            job_title="DevOps Engineer",
            orp_month=MONTH,
            **values,
        )
        session.add(application)
        await session.flush()
        return application.id


def answered(status: str, days: int) -> dict[str, Any]:
    return {"status": status, "status_at": SENT + timedelta(days=days)}


async def test_insights_and_orp_summary(api: AsyncClient, runtime: Runtime) -> None:
    contacted = await add(runtime, "Jobup 1 SA", source="jobup", score=85, **answered("refus", 2))
    await add(runtime, "Jobup 2 SA", source="jobup", score=85, **answered("refus", 9))
    await add(
        runtime,
        "Jobup 3 SA",
        source="jobup",
        score=85,
        interview_at=datetime.now(UTC),
        **answered("entretien", 7),
    )
    await add(runtime, "Jobup 4 SA", source="jobup", score=85, **answered("engagement", 12))
    for n in (5, 6):
        await add(runtime, f"Jobup {n} SA", source="jobup", score=85)
    for n in range(1, 6):
        await add(runtime, f"Indeed {n} SA", source="indeed", status="sans_reponse")
    await add(runtime, "Visée SA", spontaneous=True, followed_up_at=SENT + timedelta(days=11))
    await add(runtime, "Main SA", status="refus")
    async with runtime.sessionmaker.begin() as session:
        session.add(
            Contact(application_id=contacted, role="team", channel="email", contacted_on=SENT)
        )

    found = (await api.get("/api/insights")).json()
    assert found["funnel"] == {
        "received": 11,
        "retained": 6,
        "applications": 13,
        "responses": 5,
        "interviews": 2,
        "engagements": 1,
    }
    assert found["delay"] == {"typical": 8, "shortest": 2, "longest": 12}
    groups = {c["key"]: {g["key"]: g for g in c["groups"]} for c in found["comparisons"]}
    assert (groups["source"]["jobup"]["responses"], groups["source"]["jobup"]["total"]) == (4, 6)
    assert groups["source"]["spontaneous"]["label"] == "spontanée"
    assert groups["source"]["manual"]["enough"] is False
    # Ni les spontanées ni les candidatures à la main n'ont de note.
    assert sum(g["total"] for g in groups["score"].values()) == 11
    assert groups["contact"]["with"]["total"] == 1
    assert groups["follow_up"]["yes"]["total"] == 1
    assert found["headline"] == (
        "Les offres de jobup obtiennent plus souvent une réponse (4 sur 6, contre 0 sur 5)."
    )
    assert found["orp_summary"] is None

    month = (await api.get("/api/insights", params={"period": "month", "month": MONTH})).json()
    summary = month["orp_summary"]
    assert "13 candidatures, dont 1 spontanée." in summary
    assert (
        "5 réponses, 2 entretiens (Jobup 3 SA, Jobup 4 SA), 1 engagement (Jobup 4 SA)." in summary
    )
    assert "Sources : jobup 6, Indeed 5" in summary and "spontanées 1" in summary
    assert (await api.get("/api/insights", params={"period": "month"})).status_code == 422


async def test_relaunched_application_keeps_its_date_after_an_answer(
    api: AsyncClient, runtime: Runtime
) -> None:
    application_id = await add(runtime, "Relancée SA")
    url = f"/api/applications/{application_id}"
    marked = (await api.post(f"{url}/follow-up")).json()
    body = {k: marked[k] for k in ("sent_at", "method", "company", "job_title")}
    refused = (await api.put(url, json={**body, "status": "refus"})).json()
    assert refused["followed_up_at"] == marked["followed_up_at"]


def test_headline_needs_enough_and_a_clear_gap() -> None:
    def group(key: str, responses: int, total: int) -> Group:
        return Group(key, key, f"Les {key}", responses, total)

    few = Comparison("contact", "c", [group("avec", 3, 4), group("sans", 0, 20)])
    assert headline([few]) is None
    close = Comparison("contact", "c", [group("avec", 3, 6), group("sans", 2, 6)])
    assert headline([close]) is None
    clear = Comparison("contact", "c", [group("avec", 4, 6), group("sans", 2, 10)])
    assert (
        headline([clear])
        == "Les avec obtiennent plus souvent une réponse (4 sur 6, contre 2 sur 10)."
    )
