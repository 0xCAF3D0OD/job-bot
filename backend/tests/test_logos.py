"""Logos des entreprises (docs/14 §4) : formats, garde-fous, téléchargement, API. Sans réseau."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import CompanyLogo, Offer, OfferStatus
from jobbot.llm import alert
from jobbot.logos import service as logos
from jobbot.runtime import Runtime
from jobbot.settings import Settings
from jobbot.sources.jobup_page import parse_jobup_page

from .test_enrich import URL, page

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)


def test_sniff_accepts_images_and_rejects_the_rest() -> None:
    assert logos.sniff(PNG) == "image/png"
    assert logos.sniff(b"\xff\xd8\xff\xe0rest") == "image/jpeg"
    assert logos.sniff(b'<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>') == "image/svg+xml"
    assert logos.sniff(b"<svg><script>alert(1)</script></svg>") is None
    assert logos.sniff(b'<svg onload="x()"></svg>') is None
    assert logos.sniff(b"<html>pas une image</html>") is None


async def test_check_host_refuses_non_public_addresses() -> None:
    for url in (
        "http://exemple.ch/logo.png",
        "https://localhost/x.png",
        "https://127.0.0.1/x.png",
        "https://intranet.local/x",
    ):
        with pytest.raises(logos.Refused):
            await logos._check_host(url)


def test_jobup_page_gives_logo_and_website() -> None:
    org = (
        '"hiringOrganization": {"@type": "Organization", "name": "Acme",'
        ' "sameAs": "https://www.acme.example/", "logo": "https://media.jobup.ch/logo.jpg"},'
        ' "employmentType"'
    )
    parsed = parse_jobup_page(page("jobup-externe.html").replace('"employmentType"', org, 1), URL)
    assert (parsed.logo, parsed.website) == (
        "https://media.jobup.ch/logo.jpg",
        "https://www.acme.example/",
    )


def test_alert_logo_is_an_image_of_the_email() -> None:
    prepared = alert.AlertInput(
        text="x",
        links=["https://www.linkedin.com/jobs/view/1/"],
        images=[("https://media.licdn.com/acme.png", "Acme")],
    )
    output = (
        '{"offers": [{"title": "DevOps", "company": "Acme", "location": null,'
        ' "rate": null, "link": 1, "logo": 1}]}'
    )
    [offer] = alert.parse_output(output, prepared, None).offers
    assert offer.logo_url == "https://media.licdn.com/acme.png"
    bad = output.replace('"logo": 1', '"logo": 7')
    assert alert.parse_output(bad, prepared, None).offers[0].logo_url is None


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, company_logos, companies CASCADE"))
    yield runtime


async def add(rt: Runtime, n: int, company: str, **extra: Any) -> int:
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"logo{n}",
            title="DevOps",
            company=company,
            first_seen_at=NOW,
            last_seen_at=NOW,
            status=OfferStatus.TO_REVIEW,
            **extra,
        )
        session.add(offer)
        await session.flush()
        return offer.id


async def test_fetch_logos_and_serve(
    rt: Runtime, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    requested: list[str] = []
    home = (
        b'<html><head><link rel="icon" href="/fav.ico">'
        b'<link rel="apple-touch-icon" sizes="180x180" href="/apple.png"></head></html>'
    )

    async def fake_get(_client: object, url: str, _limit: int) -> tuple[bytes, str]:
        requested.append(url)
        if url == "https://www.beta.example/":
            return home, url
        if url.endswith((".png", ".jpg")):
            return PNG, url
        raise logos.Refused("inconnu")

    monkeypatch.setattr(logos, "_get", fake_get)
    with_logo = await add(rt, 1, "Acme SA", logo_url="https://media.jobup.ch/acme.jpg")
    same_company = await add(rt, 2, "ACME", company_website="https://www.acme.example/")
    from_site = await add(rt, 3, "Beta Sàrl", company_website="https://www.beta.example/jobs")
    nothing = await add(rt, 4, "Gamma SA")

    result = await logos.fetch_logos(rt)
    assert (result.examined, result.found, result.missing) == (3, 2, 1)
    assert "https://www.beta.example/apple.png" in requested  # la plus grande icône déclarée
    async with rt.sessionmaker() as session:
        rows = {r.name_key: r for r in await session.scalars(select(CompanyLogo))}
    assert rows["acme"].source == "page" and rows["beta"].source == "site"
    assert rows["gamma"].storage_key is None

    requested.clear()
    await logos.fetch_logos(rt)
    assert requested == []  # une seule tentative par entreprise

    app = create_app(settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        offers = {o["id"]: o for o in (await api.get("/api/offers")).json()["items"]}
        assert offers[with_logo]["has_logo"] and offers[same_company]["has_logo"]
        assert offers[from_site]["has_logo"] and not offers[nothing]["has_logo"]
        response = await api.get(f"/api/offers/{with_logo}/logo")
        assert response.status_code == 200 and response.content == PNG
        assert response.headers["content-type"] == "image/png"
        assert "default-src 'none'" in response.headers["content-security-policy"]
        assert (await api.get(f"/api/offers/{nothing}/logo")).status_code == 404
