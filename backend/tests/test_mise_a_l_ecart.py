"""« Écartée le 12 nov. » (§30 du 16.11, décision de Kevin du 16.11.2026, 13 h 53) : la date de mise à
l'écart est posée à chaque mise à l'écart (la personne, Trier, l'assistant, les critères), vidée par
« Remettre dans le tri », reposée par une nouvelle mise à l'écart ; pas de rattrapage."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

from jobbot.api.app import create_app
from jobbot.db.models import Offer, OfferStatus
from jobbot.runtime import Runtime

from .test_scoring import add_offer, ai  # noqa: F401


@pytest.fixture
async def api(ai: Runtime) -> AsyncIterator[AsyncClient]:  # noqa: F811
    app = create_app(ai.settings, ai)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def set_aside_at(rt: Runtime, offer_id: int) -> datetime | None:
    async with rt.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        assert offer is not None
        return offer.set_aside_at


def recent(value: datetime | None) -> bool:
    return value is not None and datetime.now(UTC) - value < timedelta(minutes=1)


async def test_discard_stamps_the_date_and_back_to_triage_clears_it(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
) -> None:
    offer = await add_offer(ai, 1)
    assert await set_aside_at(ai, offer) is None
    await api.patch(f"/api/offers/{offer}/status", json={"status": "ignored"})
    assert recent(await set_aside_at(ai, offer))
    shown = (await api.get(f"/api/offers/{offer}")).json()
    assert shown["set_aside_at"] is not None
    await api.patch(f"/api/offers/{offer}/status", json={"status": "to_review"})
    assert await set_aside_at(ai, offer) is None
    assert (await api.get(f"/api/offers/{offer}")).json()["set_aside_at"] is None


async def test_a_new_discard_stamps_a_new_date(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
) -> None:
    offer = await add_offer(ai, 1)
    await api.patch(f"/api/offers/{offer}/status", json={"status": "ignored"})
    old = datetime(2026, 11, 12, 9, 0, tzinfo=UTC)
    async with ai.sessionmaker.begin() as session:
        await session.execute(update(Offer).where(Offer.id == offer).values(set_aside_at=old))
    # Réécrire le même état ne touche pas la date.
    await api.patch(f"/api/offers/{offer}/status", json={"status": "ignored"})
    assert await set_aside_at(ai, offer) == old
    await api.patch(f"/api/offers/{offer}/status", json={"status": "later"})
    assert await set_aside_at(ai, offer) is None
    await api.patch(f"/api/offers/{offer}/status", json={"status": "ignored"})
    assert recent(await set_aside_at(ai, offer))


async def test_criteria_stamp_and_clear_the_date(
    api: AsyncClient,
    ai: Runtime,  # noqa: F811
) -> None:
    offer = await add_offer(ai, 1, status=OfferStatus.NEW)
    criteria = (await api.get("/api/criteria")).json()
    await api.put("/api/criteria", json={**criteria, "banned_words": ["offre"]})
    async with ai.sessionmaker() as session:
        stored = await session.get(Offer, offer)
        assert stored is not None and stored.status == OfferStatus.FILTERED_OUT
    assert recent(await set_aside_at(ai, offer))
    await api.put("/api/criteria", json={**criteria, "banned_words": []})
    async with ai.sessionmaker() as session:
        stored = await session.get(Offer, offer)
        assert stored is not None and stored.status == OfferStatus.TO_REVIEW
    assert await set_aside_at(ai, offer) is None
