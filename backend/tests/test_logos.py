"""Logos des entreprises (docs/14 §4) : formats, garde-fous, téléchargement, API. Sans réseau."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import CompanyLogo, Offer, OfferStatus
from jobbot.llm import alert
from jobbot.logos import generic
from jobbot.logos import service as logos
from jobbot.runtime import Runtime
from jobbot.settings import Settings
from jobbot.sources.jobup_page import parse_jobup_page

from .conftest import admin_engine
from .test_enrich import URL, page
from .test_logos_generic import logo

PNG = logo()
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
    async with admin_engine().begin() as conn:
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


async def test_fetch_refuses_an_image_shared_by_two_other_companies(
    rt: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Le même carré pour trois entreprises : c'est l'image de la source, pas un logo."""

    async def fake_get(_client: object, url: str, _limit: int) -> tuple[bytes, str]:
        return PNG, url

    monkeypatch.setattr(logos, "_get", fake_get)
    for n, company in enumerate(("Klanik", "adesso Schweiz AG", "SpeciTec SA"), start=1):
        await add(rt, n, company, logo_url=f"https://media.licdn.com/{n}.png")
    result = await logos.fetch_logos(rt)
    assert (result.found, result.missing) == (2, 1)
    async with rt.sessionmaker() as session:
        rows = (await session.scalars(select(CompanyLogo))).all()
    assert {r.sha256 for r in rows} == {generic.sha256(PNG)}  # gardée même refusée
    assert sorted(r.storage_key is None for r in rows) == [False, False, True]


async def test_fetch_refuses_banned_and_blank_images(
    rt: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image

    from .test_logos_generic import png

    blank = png(Image.new("RGB", (64, 64), "white"))
    images = {"https://x.example/banned.png": PNG, "https://x.example/blank.png": blank}

    async def fake_get(_client: object, url: str, _limit: int) -> tuple[bytes, str]:
        return images[url], url

    monkeypatch.setattr(logos, "_get", fake_get)
    monkeypatch.setattr(generic, "BANNED", frozenset({generic.sha256(PNG)}))
    await add(rt, 1, "Alpha", logo_url="https://x.example/banned.png")
    await add(rt, 2, "Beta", logo_url="https://x.example/blank.png")
    result = await logos.fetch_logos(rt)
    assert (result.found, result.missing) == (0, 2)


async def test_clean_generic_removes_refused_logos(
    rt: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image

    from .test_logos_generic import png

    blank = png(Image.new("RGB", (64, 64), "white"))
    other = logo(48)
    old = NOW - timedelta(days=3)
    stored = {
        "klanik": PNG,
        "adesso": PNG,
        "specitec": PNG,  # la même image pour trois entreprises
        "vide": blank,
        "acme": other,
    }
    async with rt.sessionmaker.begin() as session:
        for key, data in stored.items():
            rt.storage.put(f"logos/{key}.png", data)
            session.add(
                CompanyLogo(
                    name_key=key,
                    storage_key=f"logos/{key}.png",
                    media_type="image/png",
                    source="email",
                    checked_at=old,
                )
            )

    trial = await logos.clean_generic(rt, dry_run=True)
    assert trial.examined == 5 and len(trial.removed) == 4
    assert rt.storage.exists("logos/klanik.png")
    async with rt.sessionmaker() as session:
        assert (await session.get(CompanyLogo, "vide")).storage_key is not None  # type: ignore[union-attr]

    result = await logos.clean_generic(rt)
    assert dict(result.removed) == {
        "klanik": "image commune à plusieurs entreprises",
        "adesso": "image commune à plusieurs entreprises",
        "specitec": "image commune à plusieurs entreprises",
        "vide": "une seule couleur",
    }
    async with rt.sessionmaker() as session:
        rows = {r.name_key: r for r in await session.scalars(select(CompanyLogo))}
    assert rows["acme"].storage_key == "logos/acme.png" and rows["acme"].checked_at == old
    for key in ("klanik", "adesso", "specitec", "vide"):
        assert rows[key].storage_key is None and rows[key].source is None
        assert rows[key].checked_at > old  # pas retentée avant RETRY_AFTER
        assert not rt.storage.exists(f"logos/{key}.png")
    assert rows["klanik"].sha256 == generic.sha256(PNG)  # reconnue chez une 4e entreprise

    # Pas de nouvelle tentative avant RETRY_AFTER : l'interface montre l'initiale.
    requested: list[str] = []

    async def fake_get(_client: object, url: str, _limit: int) -> tuple[bytes, str]:
        requested.append(url)
        return PNG, url

    monkeypatch.setattr(logos, "_get", fake_get)
    await add(rt, 1, "Klanik", logo_url="https://media.licdn.com/k.png")
    await logos.fetch_logos(rt)
    assert requested == []
