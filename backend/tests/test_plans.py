"""Les formules (docs/125) : ce qui est compté, les limites, la note des offres dans la limite,
la formule vue par la personne et réglée par l'exploitant."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot import accounts, plans
from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.db.models import InterviewPractice, LlmCall, Offer, User
from jobbot.runtime import Runtime
from jobbot.scoring.service import within_plan

from .conftest import admin_engine, make_settings

PASSWORD = "un-mot-de-passe-solide"
NAME = "camille-formule"


@pytest.fixture
async def guest() -> AsyncIterator[tuple[Runtime, int]]:
    runtime = Runtime.create(make_settings(auth_enabled=True, anthropic_api_key="sk-test"))
    async with runtime.sessionmaker.begin() as session:
        user = User(username=NAME, password_hash=passwords.hash_password(PASSWORD))
        session.add(user)
        await session.flush()
        user_id = user.id
    yield runtime, user_id
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM llm_calls WHERE user_id = :u"), {"u": user_id})
        await conn.execute(
            text("DELETE FROM interview_practices WHERE user_id = :u"), {"u": user_id}
        )
        await conn.execute(text("DELETE FROM offers WHERE user_id = :u"), {"u": user_id})
        await conn.execute(text("DELETE FROM users WHERE id = :u"), {"u": user_id})
    await runtime.dispose()


def call(purpose: str, offer_id: int | None = None) -> LlmCall:
    return LlmCall(
        purpose=purpose, offer_id=offer_id, model="m", cost_usd=Decimal(0), cost_chf=Decimal(0)
    )


def offer(n: int) -> Offer:
    now = datetime.now(UTC)
    return Offer(
        fingerprint=f"formule-{n}", title=f"Offre {n}", first_seen_at=now, last_seen_at=now
    )


async def test_counts_and_messages(guest: tuple[Runtime, int]) -> None:
    runtime, user_id = guest
    with accounts.use(user_id):
        async with runtime.sessionmaker.begin() as session:
            session.add_all([call("letter") for _ in range(10)] + [call("cv")])
            session.add(InterviewPractice(kind="type", tone="neutre", language="fr", turns=[]))
        async with runtime.sessionmaker() as session:
            assert await plans.plan_of(session) == plans.ESSENTIEL
            left = {u.key: u.left for u in await plans.usage(session)}
            assert left == {"score": 150, "letter": 0, "cv": 9, "chat": 30, "practice": 0}
            await plans.check(session, plans.CV)
            with pytest.raises(plans.LimitReached) as letters:
                await plans.check(session, plans.LETTER)
            with pytest.raises(plans.LimitReached) as practice:
                await plans.check(session, plans.PRACTICE)
    day = plans.resets_on()
    month = plans.MONTHS[day.month - 1]
    assert (
        str(letters.value)
        == f"Les 10 lettres du mois sont utilisées : elles reviennent le 1er {month}."
    )
    assert str(practice.value) == (
        f"L'entraînement à l'entretien du mois est utilisé : il revient le 1er {month}."
    )


def test_resets_on_the_first_of_next_month() -> None:
    assert plans.resets_on(datetime(2026, 12, 15, tzinfo=UTC)) == date(2027, 1, 1)
    assert plans.resets_on(datetime(2026, 10, 22, tzinfo=UTC)) == date(2026, 11, 1)


async def test_scoring_stays_within_the_plan(
    guest: tuple[Runtime, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Une offre déjà notée ce mois se renote sans compter ; les nouvelles, dans la limite."""
    runtime, user_id = guest
    monkeypatch.setitem(plans.LIMITS[plans.ESSENTIEL], plans.SCORE, 2)
    with accounts.use(user_id):
        async with runtime.sessionmaker.begin() as session:
            offers = [offer(n) for n in range(3)]
            session.add_all(offers)
            await session.flush()
            session.add(call("score", offers[0].id))
        async with runtime.sessionmaker() as session:
            allowed, left_out = await within_plan(session, offers)
            assert [o.id for o in allowed] == [offers[0].id, offers[1].id] and left_out
            session.add(call("score", offers[1].id))
            await session.flush()
            allowed, left_out = await within_plan(session, [offers[0], offers[2]])
            assert [o.id for o in allowed] == [offers[0].id] and left_out


async def test_plan_seen_by_the_guest_and_set_by_the_owner(guest: tuple[Runtime, int]) -> None:
    runtime, user_id = guest
    app = create_app(runtime.settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        await api.post("/api/auth/login", json={"username": NAME, "password": PASSWORD})
        seen = (await api.get("/api/plan")).json()
    assert seen["plan"] == "essentiel" and seen["unlimited"] is False
    assert seen["plus_price_chf"] == 7
    assert seen["usage"][1]["limit_text"].startswith("Les 10 lettres du mois sont utilisées")
    assert [(u["key"], u["used"], u["limit"]) for u in seen["usage"]] == [
        ("score", 0, 150), ("letter", 0, 10), ("cv", 0, 10), ("chat", 0, 30), ("practice", 0, 1)
    ]  # fmt: skip
    # L'exploitant passe le compte en Plus (sans paiement, docs/125 §5).
    owner = Runtime.create(make_settings())
    owner_app = create_app(owner.settings, owner)
    async with AsyncClient(
        transport=ASGITransport(app=owner_app), base_url="http://localhost"
    ) as api:
        changed = await api.patch(f"/api/platform/accounts/{user_id}", json={"plan": "plus"})
        assert changed.status_code == 200
        row = next(a for a in changed.json()["accounts"] if a["id"] == user_id)
        assert row["plan"] == "plus"
        # L'exploitant n'a pas de limite.
        mine = (await api.get("/api/plan")).json()
        assert mine["unlimited"] is True and all(u["limit"] is None for u in mine["usage"])
    await owner.dispose()
    with accounts.use(user_id):
        async with runtime.sessionmaker() as session:
            assert await plans.plan_of(session) == plans.PLUS
            assert await plans.left(session, plans.LETTER) == 60
            assert await session.scalar(select(User.plan).where(User.id == user_id)) == "plus"
