"""Filtres d'affichage de la page Offres (docs/06 §7)."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.db.models import Evaluation, Offer, OfferLink, OfferStatus
from jobbot.followups.service import local_today
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import admin_engine

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
    async with admin_engine().begin() as conn:
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
    assert body["counts"] == {
        "to_review": 1,
        "filtered_out": 0,
        "later": 0,
        "in_progress": 0,
        "expired": 0,
        "all": 1,
    }
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
    assert (await api.get("/api/offers", params={"sources": "Monster!"})).status_code == 422
    assert (await api.get("/api/offers", params={"min_rate": 0})).status_code == 422


async def test_sort_by_last_activity(api: AsyncClient, runtime: Runtime) -> None:
    from datetime import UTC, datetime, timedelta

    from jobbot.db.models import Application, Draft, Offer, OfferStatus

    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        offers = [
            Offer(
                fingerprint=f"act{n}",
                title=title,
                first_seen_at=now - timedelta(days=30 - n),
                last_seen_at=now,
                status=status,
            )
            for n, (title, status) in enumerate(
                [
                    ("Envoyée hier", OfferStatus.APPLIED),
                    ("Lettre aujourd'hui", OfferStatus.PREPARING),
                    ("Envoyée il y a 5 jours", OfferStatus.APPLIED),
                    ("Préparation sans document", OfferStatus.PREPARING),
                ]
            )
        ]
        session.add_all(offers)
        await session.flush()
        session.add_all(
            [
                Application(
                    offer_id=offers[0].id,
                    sent_at=local_today() - timedelta(days=1),
                    method="electronique",
                    company="A",
                    job_title="x",
                    orp_month="2026-10",
                ),
                Application(
                    offer_id=offers[2].id,
                    sent_at=local_today() - timedelta(days=5),
                    method="electronique",
                    company="B",
                    job_title="y",
                    orp_month="2026-10",
                ),
                Draft(
                    offer_id=offers[1].id,
                    kind="letter",
                    version=1,
                    language="fr",
                    content={"subject": "s", "paragraphs": []},
                ),
            ]
        )
    page = (await api.get("/api/offers", params={"view": "in_progress", "sort": "activity"})).json()
    assert [o["title"] for o in page["items"]] == [
        "Lettre aujourd'hui",
        "Envoyée hier",
        "Envoyée il y a 5 jours",
        "Préparation sans document",
    ]


async def test_sort_by_day_then_score(api: AsyncClient, runtime: Runtime) -> None:
    """Par jour (heure suisse), le plus récent d'abord ; dans un jour, la mieux notée d'abord."""
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers CASCADE"))
    # 5 oct. 23 h 30 en Suisse = 21 h 30 UTC : encore le 5 ; 6 oct. 00 h 30 = 22 h 30 UTC le 5.
    rows = [
        ("Lundi matin, 60", datetime(2026, 10, 5, 6, 0, tzinfo=UTC), 60),
        ("Lundi soir, 90", datetime(2026, 10, 5, 21, 30, tzinfo=UTC), 90),
        ("Lundi midi, sans note", datetime(2026, 10, 5, 10, 0, tzinfo=UTC), None),
        ("Mardi 0 h 30, 40", datetime(2026, 10, 5, 22, 30, tzinfo=UTC), 40),
        ("Mardi, 75", datetime(2026, 10, 6, 9, 0, tzinfo=UTC), 75),
    ]
    async with runtime.sessionmaker.begin() as session:
        for n, (title, seen, score) in enumerate(rows):
            offer = Offer(
                fingerprint=f"day{n}",
                title=title,
                first_seen_at=seen,
                last_seen_at=seen,
                status=OfferStatus.TO_REVIEW,
            )
            session.add(offer)
            await session.flush()
            session.add(
                Evaluation(
                    offer_id=offer.id,
                    filter_passed=True,
                    criteria_hash="x",
                    score=score,
                    scored_at=seen if score is not None else None,
                )
            )
    assert await titles(api, sort="day") == [
        "Mardi, 75",
        "Mardi 0 h 30, 40",
        "Lundi soir, 90",
        "Lundi matin, 60",
        "Lundi midi, sans note",
    ]


async def test_remote_filter_and_label(api: AsyncClient, runtime: Runtime) -> None:
    """« Au moins partiel » et « complet » (docs/26 §4) ; un lieu « Remote » compte comme
    complet avant même la notation."""
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers CASCADE"))
    rows = [
        ("Partiel", "Lausanne", "hybrid", 2),
        ("Complet", "Genève", "full", None),
        ("Sur site", "Vevey", "onsite", None),
        ("Lieu remote", "Remote, Europe", None, None),
    ]
    async with runtime.sessionmaker.begin() as session:
        for n, (title, location, remote, days) in enumerate(rows):
            offer = Offer(
                fingerprint=f"remote{n}",
                title=title,
                location=location,
                first_seen_at=NOW + timedelta(minutes=n),
                last_seen_at=NOW,
                status=OfferStatus.TO_REVIEW,
            )
            session.add(offer)
            await session.flush()
            if remote:
                session.add(
                    Evaluation(
                        offer_id=offer.id,
                        filter_passed=True,
                        criteria_hash="x",
                        remote=remote,
                        remote_days=days,
                    )
                )
    assert sorted(await titles(api, remote="partial")) == ["Complet", "Lieu remote", "Partiel"]
    assert sorted(await titles(api, remote="full")) == ["Complet", "Lieu remote"]
    body = (await api.get("/api/offers", params={"view": "to_review"})).json()
    by_title = {o["title"]: o for o in body["items"]}
    assert (by_title["Partiel"]["remote"], by_title["Partiel"]["remote_days"]) == ("hybrid", 2)
    assert (
        by_title["Lieu remote"]["remote"] == "full" and by_title["Sur site"]["remote"] == "onsite"
    )


async def test_score_range_and_curve(api: AsyncClient, runtime: Runtime) -> None:
    """Note entre deux bornes, et courbe des notes sans le filtre de note (docs/27 §3)."""
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE offers CASCADE"))
    async with runtime.sessionmaker.begin() as session:
        for n, score in enumerate([42, 63, 64, 88, 100, None]):
            offer = Offer(
                fingerprint=f"curve{n}",
                title=f"Note {score}",
                first_seen_at=NOW + timedelta(minutes=n),
                last_seen_at=NOW,
                status=OfferStatus.TO_REVIEW,
            )
            session.add(offer)
            await session.flush()
            session.add(
                Evaluation(
                    offer_id=offer.id,
                    filter_passed=True,
                    criteria_hash="x",
                    score=score,
                    scored_at=NOW if score is not None else None,
                )
            )
    assert sorted(await titles(api, min_score=60, max_score=90)) == [
        "Note 63",
        "Note 64",
        "Note 88",
    ]
    body = (
        await api.get("/api/offers", params={"view": "to_review", "min_score": 60, "max_score": 90})
    ).json()
    curve = body["facets"]["scores"]
    assert len(curve) == 20 and sum(curve) == 5  # tout, sans le filtre de note
    assert curve[8] == 1 and curve[12] == 2 and curve[17] == 1 and curve[19] == 1
    assert body["facets"]["unscored"] == 1
