"""Offres expirées : page jobup introuvable, revérification, ancienneté, affichage (docs/10 §1)."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

from jobbot.api.app import create_app
from jobbot.db.models import EnrichStatus, Offer, OfferStatus
from jobbot.enrich.service import FetchResult, enrich
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .test_enrich import FakeWeb, add, fresh, get, web

__all__ = ["fresh", "web"]  # fixtures partagées avec test_enrich


def url(n: int) -> str:
    return f"https://www.jobup.ch/fr/emplois/detail/{n:08d}-0000-4000-8000-000000000000/"


async def set_values(runtime: Runtime, offer_id: int, **values: object) -> None:
    async with runtime.sessionmaker.begin() as session:
        await session.execute(update(Offer).where(Offer.id == offer_id).values(**values))


async def test_new_offer_gone_or_redirected(fresh: Runtime, web: FakeWeb) -> None:
    gone = await add(fresh, 1)
    redirected = await add(fresh, 2)
    web.responses[url(1)] = FetchResult(410, "", url(1))
    web.responses[url(2)] = FetchResult(
        200, "<html>liste</html>", "https://www.jobup.ch/fr/emplois/"
    )
    result = await enrich(fresh)
    assert result.expired == 2
    for offer_id in (gone, redirected):
        offer = await get(fresh, offer_id)
        assert offer.enrich_status == EnrichStatus.EXPIRED
        assert offer.expired_at is not None and offer.expiry_source == "page"


async def test_recheck_every_three_days(fresh: Runtime, web: FakeWeb) -> None:
    now = datetime.now(UTC)
    old = now - timedelta(days=4)
    still = await add(fresh, 1, status=OfferStatus.LATER)
    removed = await add(fresh, 2, status=OfferStatus.PREPARING)
    recent = await add(fresh, 3)
    sent = await add(fresh, 4, status=OfferStatus.APPLIED)
    for offer_id in (still, removed, sent):
        await set_values(fresh, offer_id, enrich_status=EnrichStatus.OK, enriched_at=old)
    await set_values(fresh, recent, enrich_status=EnrichStatus.OK, enriched_at=now)
    web.responses[url(2)] = FetchResult(404, "", url(2))

    result = await enrich(fresh)
    assert result.rechecked == 2 and result.expired == 1
    assert sorted(web.calls) == [url(1), url(2)]
    assert (await get(fresh, still)).checked_at is not None
    assert (await get(fresh, still)).expired_at is None
    # En préparation : marquée expirée (l'interface affiche un bandeau, pas de masquage).
    assert (await get(fresh, removed)).expiry_source == "page"

    web.calls.clear()
    await enrich(fresh)
    assert web.calls == []  # revérifiées il y a moins de 3 jours


async def test_stale_offers_without_page(fresh: Runtime, web: FakeWeb) -> None:
    long_ago = datetime.now(UTC) - timedelta(days=31)
    indeed = await add(fresh, 1, source="indeed", url="https://ch.indeed.com/viewjob?jk=1")
    sent = await add(
        fresh,
        2,
        source="indeed",
        url="https://ch.indeed.com/viewjob?jk=2",
        status=OfferStatus.APPLIED,
    )
    recent = await add(fresh, 3, source="indeed", url="https://ch.indeed.com/viewjob?jk=3")
    for offer_id in (indeed, sent):
        await set_values(fresh, offer_id, last_seen_at=long_ago)
    await set_values(fresh, recent, last_seen_at=datetime.now(UTC))
    result = await enrich(fresh)
    assert result.stale == 1
    assert (await get(fresh, indeed)).expiry_source == "age"
    assert (await get(fresh, sent)).expired_at is None
    assert (await get(fresh, recent)).expired_at is None


@pytest.fixture
async def api(fresh: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(settings, fresh)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_listing_hides_expired(api: AsyncClient, fresh: Runtime) -> None:
    now = datetime.now(UTC)
    live = await add(fresh, 1)
    gone = await add(fresh, 2)
    preparing = await add(fresh, 3, status=OfferStatus.PREPARING)
    await set_values(fresh, gone, expired_at=now, expiry_source="page")
    await set_values(fresh, preparing, expired_at=now, expiry_source="page")

    def ids(page: dict[str, object]) -> list[int]:
        return sorted(o["id"] for o in page["items"])  # type: ignore[attr-defined]

    to_review = (await api.get("/api/offers", params={"view": "to_review"})).json()
    assert ids(to_review) == [live]
    assert ids((await api.get("/api/offers")).json()) == [live, preparing]
    expired = (await api.get("/api/offers", params={"view": "expired"})).json()
    assert ids(expired) == [gone] and expired["items"][0]["expiry_source"] == "page"
    in_progress = (await api.get("/api/offers", params={"view": "in_progress"})).json()
    assert in_progress["items"][0]["expired_at"] is not None
    counts = to_review["counts"]
    assert (counts["to_review"], counts["in_progress"], counts["expired"], counts["all"]) == (
        1,
        1,
        1,
        2,
    )
