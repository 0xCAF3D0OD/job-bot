"""Filtres d'affichage de la page Offres (docs/06 §7)."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.db.models import Offer, OfferLink, OfferStatus
from jobbot.runtime import Runtime
from jobbot.settings import Settings

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)


async def add(runtime: Runtime, n: int, title: str, sources: list[str], **extra: Any) -> None:
    async with runtime.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"o{n}",
            title=title,
            first_seen_at=NOW + timedelta(minutes=n),
            last_seen_at=NOW,
            status=extra.pop("status", OfferStatus.TO_REVIEW),
            **extra,
        )
        session.add(offer)
        await session.flush()
        for source in sources:
            session.add(OfferLink(offer_id=offer.id, source=source, url=f"https://x/{n}/{source}"))


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, searches, job_runs CASCADE"))
    await add(
        runtime,
        1,
        "Ingénieur système",
        ["jobup"],
        canton="VD",
        rate_min=80,
        rate_max=100,
        apply_kind="external",
        company="Acme SA",
        description="Linux et Ansible.",
    )
    await add(
        runtime,
        2,
        "DevOps Engineer",
        ["indeed"],
        canton="GE",
        rate_min=60,
        rate_max=60,
        snippet="Kubernetes, Terraform",
    )
    await add(
        runtime,
        3,
        "Administrateur réseau",
        ["jobup", "indeed"],
        canton="VD",
        apply_kind="jobup",
        seen_count=2,
    )
    await add(runtime, 4, "Stage DevOps", ["indeed"], canton="ZH", status=OfferStatus.FILTERED_OUT)
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def titles(api: AsyncClient, **params: Any) -> list[str]:
    body = (await api.get("/api/offers", params={"view": "to_review", **params})).json()
    return [o["title"] for o in body["items"]]


async def test_search_ignores_accents_and_case(api: AsyncClient) -> None:
    assert await titles(api, q="INGENIEUR") == ["Ingénieur système"]
    assert await titles(api, q="kubernetes") == ["DevOps Engineer"]  # dans l'extrait
    assert await titles(api, q="ansible acme") == ["Ingénieur système"]  # tous les mots
    assert await titles(api, q="50%_x") == []


async def test_sources_cantons_rate_and_external(api: AsyncClient) -> None:
    assert await titles(api, sources=["indeed"]) == ["Administrateur réseau", "DevOps Engineer"]
    assert await titles(api, cantons=["vd"]) == ["Administrateur réseau", "Ingénieur système"]
    # Taux inconnu : l'offre reste visible.
    assert await titles(api, min_rate=80) == ["Administrateur réseau", "Ingénieur système"]
    assert await titles(api, external_only=True) == ["Ingénieur système"]
    assert await titles(api, sort="popular", cantons=["VD"]) == [
        "Administrateur réseau",
        "Ingénieur système",
    ]


async def test_counts_and_facets_follow_filters(api: AsyncClient) -> None:
    body = (
        await api.get("/api/offers", params={"view": "to_review", "q": "devops", "cantons": "GE"})
    ).json()
    assert body["counts"] == {"to_review": 1, "filtered_out": 0, "all": 1}
    # La facette des cantons ignore le filtre de canton : on peut élargir le choix.
    assert body["facets"]["cantons"] == [{"value": "GE", "count": 1}]
    everything = (await api.get("/api/offers", params={"view": "to_review"})).json()
    assert everything["facets"]["cantons"] == [
        {"value": "VD", "count": 2},
        {"value": "GE", "count": 1},
    ]
    assert everything["facets"]["sources"] == [
        {"value": "indeed", "count": 2},
        {"value": "jobup", "count": 2},
    ]


async def test_invalid_parameters(api: AsyncClient) -> None:
    assert (await api.get("/api/offers", params={"sources": "monster"})).status_code == 422
    assert (await api.get("/api/offers", params={"min_rate": 0})).status_code == 422
