"""Les premiers pas (docs/128) : cinq étapes cochées d'après les données, jamais en arrière ;
le chiffre de l'équipe, des nombres seulement."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from jobbot import accounts, first_steps
from jobbot.db.base import read_only
from jobbot.db.models import (
    AlertSearch,
    AlertSetup,
    Application,
    Criterion,
    Document,
    Draft,
    Offer,
    OfferStatus,
    Search,
)
from jobbot.runtime import Runtime

from .conftest import admin_engine
from .test_platform import client as account_client
from .test_platform import invite, secured  # noqa: F401

TABLES = "offers, applications, searches, drafts, criteria, documents, alert_searches"
KEYS = "('first_steps_reached', 'first_steps_dismissed', 'first_steps_celebrated')"


@pytest.fixture
async def fresh(runtime: Runtime) -> AsyncIterator[Runtime]:
    async def clean() -> None:
        async with admin_engine().begin() as conn:
            await conn.execute(text(f"TRUNCATE {TABLES} CASCADE"))
            await conn.execute(text(f"DELETE FROM settings WHERE key IN {KEYS}"))

    await clean()
    yield runtime
    await clean()


def done(page: dict[str, Any]) -> list[str]:
    return [s["key"] for s in page["first_steps"] if s["done"]]


async def test_the_five_steps(client: AsyncClient, fresh: Runtime) -> None:
    page = (await client.get("/api/today")).json()
    keys = [s["key"] for s in page["first_steps"]]
    assert keys == ["profile", "alerts", "keep", "prepare", "sent"]
    assert done(page) == []
    assert page["has_offers"] is False and page["first_steps_dismissed"] is False

    now = datetime.now(UTC)
    async with fresh.sessionmaker.begin() as session:
        session.add(Criterion(kind="locations", value=["VD"]))
        session.add(
            Document(
                filename="cv.pdf",
                doc_type="pdf",
                size=1,
                sha256="premiers-pas",
                storage_key="cv.pdf",
                text_status="ok",
            )
        )
    assert done((await client.get("/api/today")).json()) == ["profile"]

    # Les alertes créées, aucune offre encore : on attend les premières.
    async with fresh.sessionmaker.begin() as session:
        search = AlertSearch(terms="DevOps")
        session.add(search)
        await session.flush()
        session.add(AlertSetup(search_id=search.id, site="jobup"))
    page = (await client.get("/api/today")).json()
    assert done(page) == ["profile", "alerts"] and page["has_offers"] is False

    async with fresh.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint="pp1",
            title="DevOps",
            first_seen_at=now,
            last_seen_at=now,
            status=OfferStatus.PREPARING,
        )
        session.add(offer)
        await session.flush()
        offer_id = offer.id
    page = (await client.get("/api/today")).json()
    assert done(page)[-1] == "keep" and page["has_offers"] is True
    assert page["first_steps_offer_id"] == offer_id

    async with fresh.sessionmaker.begin() as session:
        session.add(Draft(offer_id=offer_id, kind="letter", version=1, language="fr", content={}))
    assert done((await client.get("/api/today")).json())[-1] == "prepare"

    # Écartée ensuite : les étapes faites le restent.
    await client.patch(f"/api/offers/{offer_id}/status", json={"status": "ignored"})
    async with fresh.sessionmaker.begin() as session:
        await session.execute(text("DELETE FROM drafts"))
    page = (await client.get("/api/today")).json()
    assert done(page)[-1] == "prepare" and page["first_steps_finished"] is False

    async with fresh.sessionmaker.begin() as session:
        session.add(
            Application(
                sent_at=date(2026, 10, 2),
                method="electronique",
                company="Acme",
                job_title="DevOps",
                orp_month="2026-10",
            )
        )
    page = (await client.get("/api/today")).json()
    assert len(done(page)) == 5 and page["first_steps_finished"] is True
    # D'autres lectures d'Aujourd'hui (la barre d'onglets) ne la consomment pas ; une fois
    # montrée, l'interface le dit et elle ne revient plus.
    assert (await client.get("/api/today")).json()["first_steps_finished"] is True
    shown = await client.put("/api/first-steps", json={"celebrated": True})
    assert shown.status_code == 204
    assert (await client.get("/api/today")).json()["first_steps_finished"] is False

    assert (await client.put("/api/first-steps", json={"dismissed": True})).status_code == 204
    assert (await client.get("/api/today")).json()["first_steps_dismissed"] is True


async def test_an_account_that_already_applied_never_sees_the_card(
    client: AsyncClient, fresh: Runtime
) -> None:
    """Un compte d'avant la 1.1.0 : tout est fait, sans carte de réussite."""
    async with fresh.sessionmaker.begin() as session:
        session.add(
            Application(
                sent_at=date(2026, 9, 2),
                method="electronique",
                company="Acme",
                job_title="DevOps",
                orp_month="2026-09",
            )
        )
    page = (await client.get("/api/today")).json()
    assert len(done(page)) == 5 and page["first_steps_finished"] is False
    assert (await client.get("/api/today")).json()["first_steps_finished"] is False


async def test_the_team_sees_numbers_only(
    runtime: Runtime,
    secured: Runtime,  # noqa: F811
) -> None:
    async with account_client(runtime) as owner, account_client(secured) as guest:
        await invite(owner, guest)
        sent = await guest.post(
            "/api/applications",
            json={"sent_at": "2026-10-20", "company": "Acme SA", "job_title": "DevOps"},
        )
        assert sent.status_code == 201, sent.text
        stats = (await owner.get("/api/platform")).json()["first_steps"]
        assert stats == {"accounts": 1, "sent_within_week": 1, "stopped_at": [0, 0, 0, 0, 0]}
        # Un compte invité ne lit pas le chiffre, même en appelant la fonction.
        assert (await guest.get("/api/platform")).status_code == 403
    async with secured.sessionmaker.begin() as session:
        guest_id = await session.scalar(text("SELECT max(id) FROM users"))
    accounts.set_current(guest_id)
    try:
        async with secured.sessionmaker() as session:
            rows = await session.execute(text("select * from first_steps_progress('-infinity')"))
            assert rows.all() == []
    finally:
        accounts.set_current(None)


async def test_read_only_demo_reads_without_writing(fresh: Runtime) -> None:
    """La démo est en lecture seule (docs/76 §1) : les étapes se lisent, rien ne s'écrit, et un
    compte qui a déjà tout fait ne voit pas la réussite."""
    async with fresh.sessionmaker.begin() as session:
        session.add(
            Application(
                sent_at=date(2026, 9, 2),
                method="electronique",
                company="Acme",
                job_title="DevOps",
                orp_month="2026-09",
            )
        )
    with read_only():
        async with fresh.sessionmaker.begin() as session:
            steps = await first_steps.load(session)
    assert steps.reached == 5 and steps.just_finished is False
    async with admin_engine().connect() as conn:
        stored = await conn.scalar(text(f"SELECT count(*) FROM settings WHERE key IN {KEYS}"))
    assert stored == 0


async def test_search_url_until_the_first_offer(client: AsyncClient, fresh: Runtime) -> None:
    """Sans offre (docs/144) : la recherche Google Emplois de la première alerte ; plus rien
    dès qu'une offre arrive."""
    assert (await client.get("/api/today")).json()["search_url"] is None  # ni métier ni alerte
    async with fresh.sessionmaker.begin() as session:
        session.add(AlertSearch(terms="Comptable", location="Sion"))
    page = (await client.get("/api/today")).json()
    assert page["search_url"] == "https://www.google.com/search?q=Comptable+emploi+Sion&udm=8"
    async with fresh.sessionmaker.begin() as session:
        now = datetime.now(UTC)
        session.add(Offer(fingerprint="g1", title="Comptable", first_seen_at=now, last_seen_at=now))
    assert (await client.get("/api/today")).json()["search_url"] is None


def _search(message_id: str, kind: str | None = None) -> Search:
    return Search(
        source="jobup",
        message_id=message_id,
        received_at=datetime.now(UTC),
        raw_key=message_id,
        parse_status="parsed",
        kind=kind,
    )


async def test_alerts_need_an_alert_created_or_received(
    client: AsyncClient, fresh: Runtime
) -> None:
    """Étape « Alerte » (corrections du 13.11 au soir, §1, décision de Kevin du 14.11) : ni la
    recherche publique, ni ses offres, ni une offre gardée ne cochent les alertes ; « Plus tard »
    laisse l'étape ouverte jusqu'à une alerte créée ou reçue, ou à la première candidature."""
    now = datetime.now(UTC)
    async with fresh.sessionmaker.begin() as session:
        session.add(_search("public:jobup:1"))
        session.add(_search("<code@jobup.ch>", kind="code"))
        session.add(
            Offer(
                fingerprint="pub1",
                title="DevOps",
                first_seen_at=now,
                last_seen_at=now,
                status=OfferStatus.PREPARING,
            )
        )
    page = (await client.get("/api/today")).json()
    # Une offre gardée fait l'étape 3, mais l'étape des alertes reste ouverte.
    assert done(page) == ["profile", "keep"]

    async with fresh.sessionmaker.begin() as session:
        session.add(_search("<alerte@jobup.ch>"))
    assert done((await client.get("/api/today")).json()) == ["profile", "alerts", "keep"]

    async with fresh.sessionmaker.begin() as session:
        await session.execute(text("DELETE FROM searches"))
        search = AlertSearch(terms="DevOps")
        session.add(search)
        await session.flush()
        session.add(AlertSetup(search_id=search.id, site="jobup"))
    assert done((await client.get("/api/today")).json()) == ["profile", "alerts", "keep"]


async def test_the_team_count_follows_the_alert_rule(fresh: Runtime) -> None:
    """La fonction SQL (migration 0084) compte comme `first_steps._computed` : les offres de la
    recherche publique ne font pas l'étape des alertes."""
    now = datetime.now(UTC)
    async with fresh.sessionmaker.begin() as session:
        session.add(_search("public:jobup:2"))
        session.add(Offer(fingerprint="pub2", title="DevOps", first_seen_at=now, last_seen_at=now))
    async with fresh.sessionmaker() as session:
        assert await first_steps.reached(session) == 0
    async with admin_engine().connect() as conn:
        body = await conn.scalar(
            text("select prosrc from pg_proc where proname = 'first_steps_progress'")
        )
    assert "not like 'public:%'" in body and "offers t where t.user_id = u.id)" not in body
