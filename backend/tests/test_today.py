"""Page « Aujourd'hui » : liste de démarrage et point du jour (docs/10 §2 b)."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.core.orp import LOCAL_TZ, shift_month
from jobbot.db.models import Offer, OfferStatus, ProfileChunk, Setting
from jobbot.runtime import Runtime

from .conftest import make_settings


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE offers, applications, orp_months, criteria, documents, profile_chunks"
                " CASCADE"
            )
        )
        await conn.execute(
            text(
                "DELETE FROM settings WHERE key LIKE 'identity_%'"
                " OR key IN ('orp_monthly_target', 'onboarding_dismissed')"
            )
        )
    yield runtime
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM settings WHERE key IN ('orp_monthly_target', 'onboarding_dismissed')")
        )


async def client(rt: Runtime, **settings: object) -> AsyncClient:
    app = create_app(make_settings(**settings), rt)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_checklist_and_day(rt: Runtime) -> None:
    today = datetime.now(UTC).astimezone(LOCAL_TZ).date()
    async with await client(rt) as api:
        fresh = (await api.get("/api/today")).json()
        assert [i["done"] for i in fresh["checklist"]] == [False] * 6
        assert fresh["checklist_dismissed"] is False

        await api.put("/api/criteria", json={"locations": ["VD"]})
        await api.put(
            "/api/identity",
            json={"name": "Jean Exemple", "street": "Rue 1", "postcode": "1020", "city": "Renens"},
        )
        async with rt.sessionmaker.begin() as session:
            session.add(Setting(key="orp_monthly_target", value=20))
            session.add(ProfileChunk(kind="competence", title="Kubernetes", content="K3s"))
            now = datetime.now(UTC)
            session.add_all(
                [
                    Offer(
                        fingerprint="a",
                        title="A",
                        first_seen_at=now,
                        last_seen_at=now,
                        status=OfferStatus.TO_REVIEW,
                    ),
                    Offer(
                        fingerprint="b",
                        title="B",
                        first_seen_at=now,
                        last_seen_at=now,
                        status=OfferStatus.TO_REVIEW,
                        expired_at=now,
                        expiry_source="page",
                    ),
                ]
            )
        old = today - timedelta(days=12)
        year, month = (int(x) for x in shift_month(f"{today:%Y-%m}", -1).split("-"))
        last_month = date(year, month, 15)
        for sent_at in (old, today, last_month):
            await api.post(
                "/api/applications",
                json={"sent_at": sent_at.isoformat(), "company": "Acme SA", "job_title": "DevOps"},
            )

        day = (await api.get("/api/today")).json()
        done = {i["key"]: i["done"] for i in day["checklist"]}
        # Pas encore de document déposé : le profil n'est pas complet.
        assert done == {
            "criteria": True,
            "profile": False,
            "identity": True,
            "orp_target": True,
            "notifications": False,
            "imap": False,
        }
        assert day["to_review"] == 1
        assert day["month_target"] == 20
        assert day["month_count"] == (2 if old.month == today.month else 1)
        # 12 jours et au moins 14 jours : les deux sont à relancer.
        assert day["to_follow_up"] == 2
        assert day["orp_due_month"] == f"{last_month:%Y-%m}"

        assert (await api.put("/api/onboarding", json={"dismissed": True})).status_code == 204
        assert (await api.get("/api/today")).json()["checklist_dismissed"] is True
