"""Agences de placement (section 35 du 16.11) : détection sans IA, correction, doublon."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot import accounts
from jobbot.agency import agency_condition, agency_kind
from jobbot.api.app import create_app
from jobbot.db.models import Application, Offer, OfferLink, Setting, User
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import admin_engine

NOW = datetime.now(UTC)


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers, applications CASCADE"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'not_agencies'"))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers, applications CASCADE"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'not_agencies'"))


async def add(runtime: Runtime, key: str, title: str, company: str | None, **extra: Any) -> int:
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=key,
            title=title,
            company=company,
            location=extra.pop("location", "Genève, GE"),
            first_seen_at=NOW,
            last_seen_at=NOW,
            seen_since=NOW,
            **extra,
        )
        session.add(offer)
        await session.flush()
        session.add(OfferLink(offer_id=offer.id, source="jobup", url=f"https://x/{key}"))
        return offer.id


async def listing(api: AsyncClient, **params: Any) -> dict[str, Any]:
    response = await api.get("/api/offers", params={"view": "all", **params})
    return {o["title"]: o for o in response.json()["items"]}


CASES = [
    ("Adecco Human Resources SA", None, "known"),
    ("Randstad (Schweiz) AG", "", "known"),
    ("Galaxi Consulting", "Pour notre client, une banque genevoise, nous cherchons…", "probable"),
    ("Galaxi Consulting", "Im Auftrag unseres Kunden suchen wir", "probable"),
    ("Galaxi Consulting", "Für unseren Kunden suchen wir", "probable"),
    ("Galaxi Consulting", "We are hiring on behalf of our client.", "probable"),
    ("Hayslab Sàrl", None, None),  # « hays » collé à un autre mot : pas l'agence
    ("Exemple SA", "Rejoins notre équipe et nos clients.", None),
    (None, None, None),
]


@pytest.mark.parametrize(("company", "description", "kind"), CASES)
async def test_python_and_sql_agree(
    runtime: Runtime, api: AsyncClient, company: str | None, description: str | None, kind: str
) -> None:
    """La pastille (Python) et le filtre (SQL) marquent les mêmes offres."""
    offer_id = await add(runtime, "c", "Ingénieur", company, description=description)
    async with runtime.sessionmaker() as session:
        offer = await session.get_one(Offer, offer_id)
        in_sql = await session.scalar(
            select(Offer.id).where(Offer.id == offer_id, agency_condition(frozenset()))
        )
    assert agency_kind(offer, frozenset()) == kind
    assert (in_sql is not None) == (kind is not None)


async def test_agency_chip_filter_and_correction(api: AsyncClient, runtime: Runtime) -> None:
    await add(runtime, "a1", "DevOps", "Adecco SA")
    probable = await add(
        runtime, "a2", "SRE", "Galaxi Consulting", snippet="Pour notre client, à Genève"
    )
    await add(runtime, "a3", "Data", "Exemple SA")
    await add(runtime, "a4", "Ancienne", "Placement SA", employer_status="agency")
    found = await listing(api)
    assert found["DevOps"]["agency"] == "known"
    assert found["SRE"]["agency"] == "probable"
    assert found["Ancienne"]["agency"] == "probable"
    assert found["Data"]["agency"] is None
    # Le doute « Employeur caché » suit la même détection.
    assert "agence" in found["SRE"]["doubts"][0]["text"]
    assert sorted(await listing(api, hide_agencies=True)) == ["Data"]

    # « Ce n'est pas une agence » : gardé pour l'entreprise, la pastille et le doute partent.
    marked = (await api.post(f"/api/offers/{probable}/not-agency")).json()
    assert marked["agency"] is None and marked["doubts"] == []
    other = await add(runtime, "a5", "Cloud", "galaxi consulting ", snippet="for our client")
    found = await listing(api, hide_agencies=True)
    assert sorted(found) == ["Cloud", "Data", "SRE"]
    assert found["Cloud"]["agency"] is None
    async with runtime.sessionmaker() as session:
        value = await session.scalar(select(Setting.value).where(Setting.key == "not_agencies"))
    assert value == ["galaxi consulting"]
    # Revenir sur la correction.
    back = (await api.delete(f"/api/offers/{other}/not-agency")).json()
    assert back["agency"] == "probable"
    assert (await api.post("/api/offers/999999/not-agency")).status_code == 404


async def test_duplicate_application_in_the_last_90_days(
    api: AsyncClient, runtime: Runtime
) -> None:
    offer_id = await add(runtime, "d1", "DevOps Engineer (80-100 %)", "Adecco SA")
    async with runtime.sessionmaker.begin() as session:
        for title, company, location, days in [
            ("DevOps Engineer", "Banque Exemple SA", "Lausanne, VD", 5),  # autre ville
            ("DevOps Engineer", "Banque Exemple SA", "Genève", 120),  # trop ancienne
            ("Ingénieur DevOps Engineer", "Banque Exemple SA", "Genève, GE", 12),
        ]:
            sent = date.today() - timedelta(days=days)
            session.add(
                Application(
                    sent_at=sent,
                    method="electronique",
                    company=company,
                    job_title=title,
                    location=location,
                    orp_month=sent.strftime("%Y-%m"),
                )
            )
    detail = (await api.get(f"/api/offers/{offer_id}")).json()
    assert detail["agency_duplicate"]["company"] == "Banque Exemple SA"
    assert detail["agency_duplicate"]["sent_at"] == str(date.today() - timedelta(days=12))
    listed = (await listing(api))["DevOps Engineer (80-100 %)"]
    assert listed["agency_duplicate"] == detail["agency_duplicate"]


async def test_correction_of_another_account_is_404(api: AsyncClient, runtime: Runtime) -> None:
    """C-4 : un autre compte ne corrige pas l'offre, et rien n'est gardé."""
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = 'compte-agence'"))
    async with runtime.sessionmaker.begin() as session:
        guest = User(username="compte-agence", password_hash="!")
        session.add(guest)
        await session.flush()
        guest_id = guest.id
    try:
        with accounts.use(guest_id):
            other = await add(runtime, "g1", "SRE", "Adecco SA")
        assert (await api.post(f"/api/offers/{other}/not-agency")).status_code == 404
        async with runtime.sessionmaker() as session:
            assert (
                await session.scalar(select(Setting).where(Setting.key == "not_agencies")) is None
            )
    finally:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE username = 'compte-agence'"))
