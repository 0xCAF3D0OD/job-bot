"""Les actualités du métier (docs/116 §4) : la famille du métier, ses sources, ou une veille."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert, select, text

from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.db.models import NewsItem, NewsSource, User
from jobbot.news import trades
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings

PASSWORD = "un-mot-de-passe-solide"


@pytest.mark.parametrize(
    ("trade", "family"),
    [
        ("Communicante", "communication"),
        ("Chargée de communication", "communication"),
        ("Pâtissier", "restauration"),
        ("Menuisier poseur", "batiment"),
        ("Magasinier", "logistique"),
        ("Vendeuse en magasin", "commerce"),
        ("Infirmière", "sante-social"),
        ("Comptable", "finance-admin"),
        ("Ingénieur DevOps", "informatique"),
        ("Astronaute", None),
    ],
)
def test_family_of(trade: str, family: str | None) -> None:
    assert trades.family_of(trade) == family


def test_every_family_has_sources() -> None:
    for family, _ in trades._FAMILIES:
        assert trades.family_feeds(family), family


@pytest.fixture
async def secured() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(auth_enabled=True))
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = 'amy-metier'"))
        await conn.execute(
            text("DELETE FROM news_items WHERE url LIKE 'https://t.example/metier%'")
        )
    await runtime.dispose()


async def _followed(api: AsyncClient) -> set[str]:
    return {s["feed_url"] for s in (await api.get("/api/news/sources")).json()}


async def test_trade_brings_its_news(secured: Runtime) -> None:
    async with secured.sessionmaker.begin() as session:
        session.add(User(username="amy-metier", password_hash=passwords.hash_password(PASSWORD)))
    app = create_app(secured.settings, secured)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        await api.post("/api/auth/login", json={"username": "amy-metier", "password": PASSWORD})
        await api.put("/api/welcome", json={"trade": "Communicante"})
        followed = await _followed(api)
        assert {"https://www.cominmag.ch/feed/", "https://www.cbnews.fr/rss.xml"} <= followed

        # Un article de Cominmag ne dit pas « communicante » : il parle du métier quand même.
        async with admin_engine().begin() as conn:
            source_id = await conn.scalar(
                select(NewsSource.id).where(NewsSource.feed_url == "https://www.cominmag.ch/feed/")
            )
            await conn.execute(
                insert(NewsItem).values(
                    source_id=source_id,
                    title="Une agence lausannoise remporte le budget d'une marque horlogère",
                    url="https://t.example/metier-1",
                    language="fr",
                    published_at=datetime.now(UTC),
                )
            )
        mine = (await api.get("/api/news", params={"domain_only": True})).json()["items"]
        assert [i["url"] for i in mine] == ["https://t.example/metier-1"]

        # La restauration : la veille romande du catalogue.
        await api.put("/api/welcome", json={"trade": "Pâtissier"})
        assert trades.family_feeds("restauration") <= await _followed(api)
