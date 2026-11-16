"""Offres déjà postulées (décision de Kevin du 16.11.2026) : doublon sûr (même lien) rattaché,
doublon probable (même titre, même entreprise) visible avec « Déjà postulé le … »."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import Application, Offer, OfferLink
from jobbot.filtering.duplicates import group_duplicates, link_key, post_key
from jobbot.followups.service import local_today
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import admin_engine

NOW = datetime.now(UTC)
TRUNCATE = "TRUNCATE offers, applications CASCADE"


@pytest.fixture
async def api(runtime: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))
    app = create_app(settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    async with admin_engine().begin() as conn:
        await conn.execute(text(TRUNCATE))


async def offer(runtime: Runtime, key: str, url: str | None, **extra: object) -> int:
    async with runtime.sessionmaker.begin() as session:
        fields: dict[str, object] = {"status": "to_review", **extra}
        row = Offer(
            fingerprint=key,
            title="Software Engineer",
            company="EPFL",
            first_seen_at=NOW,
            last_seen_at=NOW,
            **fields,
        )
        session.add(row)
        await session.flush()
        if url:
            session.add(OfferLink(offer_id=row.id, source="jobup", url=url))
        return row.id


def test_link_key_keeps_the_offer_id_only() -> None:
    assert link_key("https://www.jobup.ch/fr/emplois/detail/abc/?utm_source=x") == (
        "jobup.ch/fr/emplois/detail/abc"
    )
    # Indeed : l'annonce est dans jk, le chemin est le même pour toutes.
    assert link_key("https://ch.indeed.com/viewjob?jk=1&from=mail") == "ch.indeed.com/viewjob?jk=1"
    assert link_key("https://ch.indeed.com/viewjob?jk=1") != link_key(
        "https://ch.indeed.com/viewjob?jk=2"
    )
    assert link_key("https://example.ch/") is None and link_key("mailto:a@b.ch") is None


def test_post_key_ignores_legal_form_rate_and_case() -> None:
    assert post_key("Software Engineer (80-100 %)", "EPFL SA") == post_key(
        "SOFTWARE ENGINEER", "epfl"
    )
    assert post_key("Software Engineer", "Müller Sàrl") == post_key("software engineer", "Muller")
    assert post_key("Software Engineer", None) is None


async def test_marking_sent_hides_the_same_page_at_once(api: AsyncClient, runtime: Runtime) -> None:
    first = await offer(runtime, "a", "https://www.jobup.ch/fr/emplois/detail/abc/")
    copy = await offer(runtime, "b", "https://jobup.ch/fr/emplois/detail/abc?utm_source=alerte")
    # Spontanée au même poste : jamais rattachée, la pastille seulement.
    spontaneous = await offer(runtime, "c", None, spontaneous=True, status="preparing")
    prefill = (await api.get(f"/api/offers/{first}/application-prefill")).json()
    sent = await api.post(
        "/api/applications", json={**prefill, "sent_at": local_today().isoformat()}
    )
    assert sent.status_code == 201

    items = {o["id"]: o for o in (await api.get("/api/offers")).json()["items"]}
    assert copy not in items
    assert items[spontaneous]["applied_before"] == local_today().isoformat()


async def test_application_typed_in_sent_finds_its_offer(
    runtime: Runtime, api: AsyncClient
) -> None:
    found = await offer(runtime, "a", "https://ch.indeed.com/viewjob?jk=42&from=mail")
    other = await offer(runtime, "b", "https://ch.indeed.com/viewjob?jk=43")
    async with runtime.sessionmaker.begin() as session:
        session.add(
            Application(
                sent_at=local_today(),
                method="electronique",
                company="EPFL",
                job_title="Software Engineer",
                orp_month=local_today().strftime("%Y-%m"),
                application_url="https://ch.indeed.com/viewjob?jk=42",
            )
        )
    async with runtime.sessionmaker.begin() as session:
        await group_duplicates(session)
    async with runtime.sessionmaker() as session:
        application = await session.scalar(select(Application))
        assert application is not None and application.offer_id == found
        assert (await session.get(Offer, found)).status == "applied"  # type: ignore[union-attr]
        assert (await session.get(Offer, other)).status == "to_review"  # type: ignore[union-attr]
