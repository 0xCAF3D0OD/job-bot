"""Page « Aujourd'hui » : le point du jour (docs/10 §2 b)."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.core.orp import LOCAL_TZ, shift_month
from jobbot.db.models import Offer, OfferStatus, ProfileChunk, Setting
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with admin_engine().begin() as conn:
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


async def test_day(rt: Runtime) -> None:
    today = datetime.now(UTC).astimezone(LOCAL_TZ).date()
    async with await client(rt) as api:
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
        assert day["to_review"] == 1
        assert day["month_target"] == 20
        assert day["month_count"] == (2 if old.month == today.month else 1)
        # 12 jours et au moins 14 jours : les deux sont à relancer.
        assert day["to_follow_up"] == 2
        # Les deux plus anciennes, pour « À faire » (docs/95) : la plus ancienne d'abord.
        follow_ups = day["follow_ups"]
        expected = sorted([old.isoformat(), last_month.isoformat()])
        assert [f["sent_at"] for f in follow_ups] == expected
        assert follow_ups[0]["company"] == "Acme SA" and follow_ups[0]["status"] == "en_attente"
        assert all(f["orp_month"] == f["sent_at"][:7] for f in follow_ups)
        assert day["orp_due_month"] == f"{last_month:%Y-%m}"


async def test_week_and_orp_history(rt: Runtime) -> None:
    """Tableau de bord (docs/54 §5) : 7 jours d'activité, les 3 mois précédents."""
    today = datetime.now(UTC).astimezone(LOCAL_TZ).date()
    now = datetime.now(UTC)
    async with rt.sessionmaker.begin() as session:
        session.add_all(
            [
                Offer(fingerprint="w1", title="A", first_seen_at=now, last_seen_at=now),
                Offer(fingerprint="w2", title="B", first_seen_at=now, last_seen_at=now),
                # Trop ancienne pour la semaine.
                Offer(
                    fingerprint="w3",
                    title="C",
                    first_seen_at=now - timedelta(days=8),
                    last_seen_at=now,
                ),
            ]
        )
    two_ago = shift_month(f"{today:%Y-%m}", -2)
    year, month = (int(x) for x in two_ago.split("-"))
    async with await client(rt) as api:
        for sent_at in (today, today - timedelta(days=3), date(year, month, 10)):
            await api.post(
                "/api/applications",
                json={"sent_at": sent_at.isoformat(), "company": "Acme SA", "job_title": "SRE"},
            )
        day = (await api.get("/api/today")).json()
    week = day["week"]
    assert [w["day"] for w in week] == [
        (today - timedelta(days=6 - i)).isoformat() for i in range(7)
    ]
    assert week[-1] == {"day": today.isoformat(), "offers": 2, "applications": 1}
    assert week[3]["applications"] == 1
    assert sum(w["offers"] for w in week) == 2
    history = {h["month"]: h["count"] for h in day["orp_history"]}
    # Rien avant la première activité du compte (1.6.62) : la première candidature date de deux
    # mois, le mois d'avant n'apparaît pas (plus de « 0 / 13 manqué »).
    assert list(history) == [shift_month(f"{today:%Y-%m}", d) for d in (-2, -1)]
    assert history[two_ago] == 1
