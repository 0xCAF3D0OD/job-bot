"""Actualités (docs/15 §2) : lecture des flux, relevé, API. Sans réseau."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import NewsSource
from jobbot.logos import service as logos
from jobbot.news import service as news
from jobbot.news.feeds import FeedError, parse_feed
from jobbot.runtime import Runtime
from jobbot.settings import Settings

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>RTS Info - Économie</title>
<item><title>Le chômage reste à 3 %</title><link>https://www.rts.ch/info/economie/1</link>
<description>&lt;p&gt;Le &lt;b&gt;SECO&lt;/b&gt; publie ses chiffres.&lt;/p&gt;&lt;img src="https://img.rts.ch/1.jpg"&gt;</description>
<pubDate>Tue, 06 Oct 2026 08:00:00 +0200</pubDate>
<author>Staatssekretariat für Wirtschaft</author></item>
<item><title>Agriculture : récoltes</title><link>https://www.rts.ch/info/economie/2</link>
<pubDate>2026-10-05</pubDate><author>Bundesamt für Landwirtschaft</author></item>
</channel></rss>""".encode()
ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
<title>KodeKloud</title>
<entry><title>CKA exam tips</title><link rel="alternate" href="https://www.youtube.com/watch?v=abc"/>
<published>2026-10-05T10:00:00+00:00</published><author><name>KodeKloud</name></author>
<media:group><media:thumbnail url="https://i.ytimg.com/vi/abc/hqdefault.jpg"/>
<media:description>How to pass the CKA.</media:description></media:group></entry>
</feed>"""
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 40


def test_parse_rss_and_atom() -> None:
    rss = parse_feed(RSS, NOW)
    assert rss.title == "RTS Info - Économie" and len(rss.items) == 2
    first = rss.items[0]
    assert first.summary == "Le SECO publie ses chiffres."
    assert first.image_url == "https://img.rts.ch/1.jpg"
    assert first.published_at == datetime(2026, 10, 6, 6, 0, tzinfo=UTC)
    atom = parse_feed(ATOM, NOW)
    [video] = atom.items
    assert (video.url, video.summary, video.image_url) == (
        "https://www.youtube.com/watch?v=abc",
        "How to pass the CKA.",
        "https://i.ytimg.com/vi/abc/hqdefault.jpg",
    )


def test_parse_refuses_entities_and_garbage() -> None:
    with pytest.raises(FeedError):
        parse_feed(b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><rss/>')
    with pytest.raises(FeedError):
        parse_feed(b"<html>pas un flux</html>")


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE news_items"))
        await conn.execute(text("UPDATE news_sources SET active = false"))
        await conn.execute(text("DELETE FROM news_sources WHERE name LIKE 'Test %'"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'news_seen_at'"))
    yield runtime
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE news_items"))
        await conn.execute(text("DELETE FROM news_sources WHERE name LIKE 'Test %'"))
        await conn.execute(text("UPDATE news_sources SET active = true"))


async def test_fetch_filters_downloads_and_serves(
    rt: Runtime, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_get(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        if url.endswith("rss"):
            return RSS, url
        if url.endswith("atom"):
            return ATOM, url
        if url.endswith(".jpg"):
            return JPEG, url
        raise logos.Refused("inconnu")

    monkeypatch.setattr(logos, "_get", fake_get)
    async with rt.sessionmaker.begin() as session:
        session.add_all(
            [
                NewsSource(
                    kind="articles",
                    name="Test SECO",
                    url="https://x",
                    feed_url="https://t.example/rss",
                    match="Staatssekretariat für Wirtschaft",
                ),
                NewsSource(
                    kind="videos",
                    name="Test vidéos",
                    url="https://y",
                    feed_url="https://t.example/atom",
                ),
                NewsSource(
                    kind="articles",
                    name="Test cassé",
                    url="https://z",
                    feed_url="https://t.example/casse",
                ),
            ]
        )
    result = await news.fetch_news(rt)
    assert (result.new_items, result.failed) == (2, 1)  # l'article agricole est filtré
    again = await news.fetch_news(rt)
    assert again.new_items == 0  # pas de doublon
    async with rt.sessionmaker() as session:
        broken = await session.scalar(select(NewsSource).where(NewsSource.name == "Test cassé"))
        assert broken is not None and broken.error

    app = create_app(settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        page = (await api.get("/api/news")).json()
        assert [i["title"] for i in page["items"]] == ["Le chômage reste à 3 %", "CKA exam tips"]
        assert (page["new_articles"], page["new_videos"]) == (1, 1)
        videos = (await api.get("/api/news", params={"kind": "videos"})).json()["items"]
        assert [v["source"] for v in videos] == ["Test vidéos"] and videos[0]["has_image"]
        image = await api.get(f"/api/news/items/{videos[0]['id']}/image")
        assert image.status_code == 200 and image.content == JPEG
        assert (await api.post("/api/news/seen")).status_code == 204
        seen = (await api.get("/api/news")).json()
        assert (seen["new_articles"], seen["new_videos"]) == (0, 0)


async def test_sources_api(
    rt: Runtime, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_resolve(url: str) -> news.ResolvedSource:
        if "youtube" in url:
            return news.ResolvedSource(
                "videos",
                "Test chaîne",
                url,
                "https://www.youtube.com/feeds/videos.xml?channel_id=UCtest",
            )
        raise news.SourceError("aucun flux RSS annoncé par cette page")

    monkeypatch.setattr("jobbot.api.routes.news.resolve", fake_resolve)
    app = create_app(settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        defaults = (await api.get("/api/news/sources")).json()
        assert {s["name"] for s in defaults} >= {"RTS Info — Économie", "KodeKloud"}
        added = await api.post("/api/news/sources", json={"url": "https://www.youtube.com/@test"})
        assert added.status_code == 201
        source = next(s for s in added.json() if s["name"] == "Test chaîne")
        assert source["kind"] == "videos"
        duplicate = await api.post(
            "/api/news/sources", json={"url": "https://www.youtube.com/@test"}
        )
        assert duplicate.status_code == 409
        bad = await api.post("/api/news/sources", json={"url": "https://pas-de-flux.example"})
        assert bad.status_code == 422 and "flux" in bad.json()["detail"]
        paused = (
            await api.patch(f"/api/news/sources/{source['id']}", json={"active": False})
        ).json()
        assert not next(s for s in paused if s["id"] == source["id"])["active"]
        left = (await api.delete(f"/api/news/sources/{source['id']}")).json()
        assert all(s["id"] != source["id"] for s in left)


async def test_resolve_youtube(monkeypatch: pytest.MonkeyPatch) -> None:
    channel = "UCSWj8mqQCcrcBlXPi4ThRDQ"
    pages: list[str] = []

    async def fake_get(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        pages.append(url)
        if "feeds/videos.xml" in url:
            return ATOM, url
        # Page de consentement aux cookies, comme YouTube la sert en Europe.
        return (
            b"<html><title>Avant d'acceder a YouTube</title></html>",
            "https://consent.youtube.com/ml",
        )

    monkeypatch.setattr(logos, "_get", fake_get)
    for given in (channel, f"https://www.youtube.com/channel/{channel}/videos"):
        pages.clear()
        source = await news.resolve(given)
        assert source.kind == "videos" and source.name == "KodeKloud"
        assert source.feed_url == f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
        assert pages == [source.feed_url]  # aucune page lue, seulement le flux
    with pytest.raises(news.SourceError, match="ID de la chaîne"):
        await news.resolve("https://www.youtube.com/@KodeKloud")
