"""« Comment ça marche » (docs/21 §3) : étapes cochées d'après les données."""

from datetime import UTC, date, datetime

from httpx import AsyncClient
from sqlalchemy import text

from jobbot.db.models import Application, Offer, OfferStatus, Search
from jobbot.runtime import Runtime


async def test_journey_steps(client: AsyncClient, runtime: Runtime) -> None:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, applications, searches, orp_months CASCADE"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'journey_dismissed'"))
    steps = lambda page: {s["key"]: s["done"] for s in page["journey"]}  # noqa: E731
    page = (await client.get("/api/today")).json()
    assert steps(page) == dict.fromkeys(["alerts", "triage", "apply", "follow", "orp"], False)
    assert page["journey_dismissed"] is False

    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        session.add(
            Search(
                source="jobup",
                message_id="<j@test>",
                received_at=now,
                raw_key="emails/j.eml",
                parse_status="parsed",
            )
        )
        offer = Offer(
            fingerprint="j1",
            title="DevOps",
            first_seen_at=now,
            last_seen_at=now,
            status=OfferStatus.LATER,
        )
        session.add(offer)
        session.add(
            Application(
                sent_at=date(2026, 10, 2),
                method="electronique",
                company="Acme",
                job_title="DevOps",
                orp_month="2026-10",
                status="entretien",
            )
        )
    done = steps((await client.get("/api/today")).json())
    assert done == {"alerts": True, "triage": True, "apply": True, "follow": True, "orp": False}

    assert (await client.put("/api/journey", json={"dismissed": True})).status_code == 204
    assert (await client.get("/api/today")).json()["journey_dismissed"] is True
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, applications, searches CASCADE"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'journey_dismissed'"))
