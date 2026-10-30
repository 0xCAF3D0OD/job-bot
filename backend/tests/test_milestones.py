"""Les étapes datées du test utilisateurs (demande de Kevin du 30.10.2026) : la première fois de
chaque étape, écrite une seule fois par la base ; l'exploitant seul les lit, sans aucun contenu."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import text

from jobbot import accounts
from jobbot.db.models import AlertSearch, AlertSetup, Draft, Offer, OrpMonth
from jobbot.runtime import Runtime

from .conftest import admin_engine
from .test_platform import client as account_client
from .test_platform import invite, secured  # noqa: F401

TABLES = "offers, searches, drafts, alert_searches, orp_months, account_milestones"


@pytest.fixture
async def fresh(runtime: Runtime) -> AsyncIterator[Runtime]:
    async def clean() -> None:
        async with admin_engine().begin() as conn:
            await conn.execute(text(f"TRUNCATE {TABLES} CASCADE"))

    await clean()
    yield runtime
    await clean()


async def milestones(runtime: Runtime) -> dict[str, datetime]:
    async with runtime.sessionmaker() as session:
        rows = await session.execute(text("select step, reached_at from account_milestones"))
        return {row.step: row.reached_at for row in rows}


async def test_each_step_is_dated_once(fresh: Runtime) -> None:
    """Alerte, offre, candidature préparée, preuves exportées : la première date, jamais
    remplacée par une plus tardive (une plus ancienne, rangée après, la corrige)."""
    first = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
    async with fresh.sessionmaker.begin() as session:
        search = AlertSearch(terms="DevOps")
        session.add(search)
        await session.flush()
        session.add(AlertSetup(search_id=search.id, site="jobup", created_at=first))
        offer = Offer(
            fingerprint="m1", title="DevOps", first_seen_at=first + timedelta(hours=5),
            last_seen_at=first,
        )  # fmt: skip
        session.add(offer)
        await session.flush()
        session.add(
            Draft(offer_id=offer.id, kind="letter", version=1, language="fr", content={},
                  created_at=first + timedelta(days=1))
        )  # fmt: skip
        session.add(OrpMonth(month="2026-10"))
    assert set(await milestones(fresh)) == {"first_alert", "first_offer", "first_prepared"}
    async with fresh.sessionmaker.begin() as session:
        await session.execute(
            text("update orp_months set exported_at = :at"), {"at": first + timedelta(days=3)}
        )
    dated = await milestones(fresh)
    assert dated == {
        "first_alert": first,
        "first_offer": first + timedelta(hours=5),
        "first_prepared": first + timedelta(days=1),
        "first_export": first + timedelta(days=3),
    }
    # Une deuxième offre, plus tard : rien ne change ; une plus ancienne, rangée après, corrige.
    async with fresh.sessionmaker.begin() as session:
        session.add(Offer(fingerprint="m2", title="SRE", first_seen_at=first + timedelta(days=9),
                          last_seen_at=first))  # fmt: skip
    assert (await milestones(fresh))["first_offer"] == first + timedelta(hours=5)
    async with fresh.sessionmaker.begin() as session:
        session.add(Offer(fingerprint="m3", title="SRE", first_seen_at=first, last_seen_at=first))
    assert (await milestones(fresh))["first_offer"] == first
    # Les tables ne gardent que l'étape et la date.
    async with admin_engine().connect() as conn:
        columns = await conn.scalars(
            text(
                "select column_name from information_schema.columns "
                "where table_name = 'account_milestones' order by ordinal_position"
            )
        )
        assert list(columns) == ["user_id", "step", "reached_at"]


async def test_the_owner_alone_reads_the_dates(
    runtime: Runtime,
    secured: Runtime,  # noqa: F811
) -> None:
    async with account_client(runtime) as owner, account_client(secured) as guest:
        await invite(owner, guest)
        prepared = await guest.post(
            "/api/applications",
            json={"sent_at": str(date.today()), "company": "Acme SA", "job_title": "DevOps"},
        )
        assert prepared.status_code == 201
        rows = (await owner.get("/api/platform")).json()["milestones"]
        assert len(rows) == 1
        assert set(rows[0]) == {
            "account", "created_at", "first_alert", "first_offer", "first_prepared",
            "first_export",
        }  # fmt: skip
        assert (await guest.get("/api/platform")).status_code == 403
    async with secured.sessionmaker.begin() as session:
        guest_id = await session.scalar(text("SELECT max(id) FROM users"))
    accounts.set_current(guest_id)
    try:
        async with secured.sessionmaker() as session:
            assert (await session.execute(text("select * from milestones_progress()"))).all() == []
    finally:
        accounts.set_current(None)
