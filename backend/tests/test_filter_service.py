from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select, text

from jobbot.api.app import create_app
from jobbot.core.filter import ContractType, Criteria
from jobbot.db.models import Evaluation, Offer, OfferStatus
from jobbot.filtering.service import load_criteria, run_filter, save_criteria
from jobbot.runtime import Runtime
from jobbot.settings import Settings

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)


@pytest.fixture
async def fresh(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, criteria, searches, job_runs CASCADE"))
    yield runtime


async def add_offer(runtime: Runtime, title: str, location: str | None, **extra: object) -> int:
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"{title}|{location}",
            title=title,
            location=location,
            first_seen_at=NOW,
            last_seen_at=NOW,
            **extra,
        )
        session.add(offer)
        await session.flush()
        return offer.id


async def statuses(runtime: Runtime) -> dict[str, str]:
    async with runtime.sessionmaker() as session:
        return {o.title: o.status for o in await session.scalars(select(Offer))}


async def test_filter_sets_statuses_and_reasons(fresh: Runtime) -> None:
    await add_offer(fresh, "Ingénieur système", "Pully, VD")
    await add_offer(fresh, "Admin", "Zürich, ZH")
    await add_offer(fresh, "Admin jobup", "Prilly")
    await add_offer(fresh, "Admin Prilly Indeed", "Prilly, VD")
    async with fresh.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(locations=("VD",)))

    result = await run_filter(fresh)

    assert (result.examined, result.to_review, result.filtered_out) == (4, 3, 1)
    async with fresh.sessionmaker() as session:
        cantons = {o.title: o.canton for o in await session.scalars(select(Offer))}
    # « Prilly » seul : canton appris de « Prilly, VD ».
    assert cantons["Admin jobup"] == "VD" and cantons["Admin"] == "ZH"
    assert (await statuses(fresh))["Admin"] == "filtered_out"
    async with fresh.sessionmaker() as session:
        evaluation = await session.scalar(
            select(Evaluation).join(Offer).where(Offer.title == "Admin")
        )
    assert evaluation is not None and not evaluation.filter_passed
    assert evaluation.filter_reasons == [
        {"rule": "locations", "message": "Lieu : Zürich, ZH n'est pas dans tes lieux acceptés"}
    ]


async def test_refilter_is_idempotent_and_follows_new_criteria(fresh: Runtime) -> None:
    await add_offer(fresh, "Stage DevOps", "Lausanne, VD")
    async with fresh.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(excluded_types=(ContractType.INTERNSHIP,)))
    await run_filter(fresh)
    await run_filter(fresh)
    assert await statuses(fresh) == {"Stage DevOps": "filtered_out"}

    async with fresh.sessionmaker.begin() as session:
        await save_criteria(session, Criteria())
    await run_filter(fresh)
    assert await statuses(fresh) == {"Stage DevOps": "to_review"}


async def test_manual_statuses_are_never_touched(fresh: Runtime) -> None:
    await add_offer(fresh, "Stage gardé", "Lausanne", status=OfferStatus.LATER)
    async with fresh.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(excluded_types=(ContractType.INTERNSHIP,)))
    result = await run_filter(fresh)
    assert result.examined == 0
    assert await statuses(fresh) == {"Stage gardé": "later"}


async def test_criteria_round_trip(fresh: Runtime) -> None:
    criteria = Criteria(locations=("VD", "Genève"), remote_ok=True, min_rate=80)
    async with fresh.sessionmaker.begin() as session:
        await save_criteria(session, criteria)
    async with fresh.sessionmaker() as session:
        assert await load_criteria(session) == criteria


# --- API -----------------------------------------------------------------------------


@pytest.fixture
def clean_queue(settings: Settings) -> Iterator[None]:
    engine = create_engine(settings.sqlalchemy_url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM procrastinate_jobs"))
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM procrastinate_jobs"))
    engine.dispose()


@pytest.fixture
async def api(fresh: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(settings, fresh)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.usefixtures("clean_queue")
async def test_api_criteria_save_and_refilter(api: AsyncClient) -> None:
    empty = (await api.get("/api/criteria")).json()
    assert empty["criteria"]["locations"] == []
    assert "internship" in empty["keywords"]["contract_types"]["stage"]

    body = {
        "locations": ["VD", " Genève ", "vd"],
        "remote_ok": True,
        "min_rate": 80,
        "excluded_types": ["stage"],
        "banned_words": ["vente"],
        "unspoken_languages": ["allemand"],
    }
    saved = (await api.put("/api/criteria", json=body)).json()["criteria"]
    assert saved["locations"] == ["VD", "Genève"]  # espaces retirés, doublons écartés
    assert (await api.get("/api/criteria")).json()["criteria"] == saved

    assert (await api.post("/api/filter")).json() == {"result": "already_queued"}
    assert (await api.put("/api/criteria", json={"min_rate": 150})).status_code == 422


async def test_api_settings(api: AsyncClient) -> None:
    defaults = (await api.get("/api/settings")).json()
    assert defaults == {
        "orp_monthly_target": None,
        "notify_score_threshold": 70,
        "llm_monthly_budget_chf": 10,
    }
    new = {"orp_monthly_target": 8, "notify_score_threshold": 75, "llm_monthly_budget_chf": 5}
    assert (await api.put("/api/settings", json=new)).json() == new
    assert (await api.get("/api/settings")).json() == new
    assert (await api.put("/api/settings", json={"notify_score_threshold": 120})).status_code == 422
    await api.put("/api/settings", json=defaults)


async def test_api_offer_views(api: AsyncClient, fresh: Runtime) -> None:
    await add_offer(fresh, "Admin", "Pully, VD")
    await add_offer(fresh, "Admin ZH", "Zürich, ZH")
    await add_offer(fresh, "Pas encore filtrée", "Bern, BE")
    async with fresh.sessionmaker.begin() as session:
        await save_criteria(session, Criteria(locations=("VD",)))
    await run_filter(fresh)
    await add_offer(fresh, "Arrivée après le filtre", "Sion, VS")

    page = (await api.get("/api/offers", params={"view": "to_review"})).json()
    assert page["counts"] == {
        "to_review": 2,
        "filtered_out": 2,
        "later": 0,
        "in_progress": 0,
        "all": 4,
    }
    assert sorted(o["title"] for o in page["items"]) == ["Admin", "Arrivée après le filtre"]
    out = (await api.get("/api/offers", params={"view": "filtered_out"})).json()
    assert out["total"] == 2
    assert all(o["filter_reasons"] for o in out["items"])
