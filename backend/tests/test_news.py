"""Actualités (docs/15 §2) : lecture des flux, relevé, API. Sans réseau."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot.api.app import create_app
from jobbot.db.models import Evaluation, NewsItem, NewsSource, Offer
from jobbot.logos import service as logos
from jobbot.news import catalog, domain, language
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


RESET = [
    "TRUNCATE news_items",
    "DELETE FROM news_sources WHERE name LIKE 'Test %'",
    "DELETE FROM profiles WHERE NOT is_main",
    "UPDATE profiles SET preferences = '{}'::jsonb, news_seen_at = NULL WHERE is_main",
]


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        for statement in RESET:
            await conn.execute(text(statement))
        # Les sources de départ restent suivies, en pause : seules celles du test sont relevées.
        await conn.execute(text("UPDATE profile_sources SET active = false"))
    yield runtime
    async with runtime.engine.begin() as conn:
        for statement in RESET:
            await conn.execute(text(statement))
        await conn.execute(text("UPDATE profile_sources SET active = true"))


async def follow_test_sources(rt: Runtime) -> None:
    """Le profil principal suit les sources « Test … » ajoutées directement en base."""
    async with rt.engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO profile_sources (profile_id, source_id, active)"
                " SELECT p.id, s.id, true FROM profiles p, news_sources s"
                " WHERE p.is_main AND s.name LIKE 'Test %' ON CONFLICT DO NOTHING"
            )
        )


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
    await follow_test_sources(rt)
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
    queued: list[str] = []

    async def fake_enqueue(_settings: Settings, name: str) -> bool:
        queued.append(name)
        return True

    monkeypatch.setattr("jobbot.api.routes.news.enqueue", fake_enqueue)
    app = create_app(settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        defaults = (await api.get("/api/news/sources")).json()
        assert {s["name"] for s in defaults} >= {"RTS Info — Économie", "KodeKloud"}
        added = await api.post("/api/news/sources", json={"url": "https://www.youtube.com/@test"})
        assert added.status_code == 201
        source = next(s for s in added.json() if s["name"] == "Test chaîne")
        assert source["kind"] == "videos" and queued == ["news"]  # relevé tout de suite
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


@pytest.fixture
def queued(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Relevés mis en file par l'API (sans file réelle)."""
    calls: list[str] = []

    async def fake_enqueue(_settings: Settings, name: str) -> bool:
        calls.append(name)
        return True

    monkeypatch.setattr("jobbot.api.routes.news.enqueue", fake_enqueue)
    return calls


def test_language_and_domain() -> None:
    assert language.detect("Le chômage reste stable en septembre selon le SECO") == "fr"
    assert language.detect("Die Arbeitslosigkeit ist im September nicht gestiegen") == "de"
    assert language.detect("How to pass the CKA exam in your first try") == "en"
    assert language.detect("Kubernetes CKA") is None
    assert language.from_feed("fr-CH") == "fr" and language.from_feed("xx") is None
    keywords = ["DevOps", "CI/CD", "Kubernetes", "SRE"]
    assert domain.matched(keywords, "Pipeline ci-cd et kubernetes", None) == [
        "CI/CD",
        "Kubernetes",
    ]
    assert domain.matched(keywords, "Kubernetesque", "SREnity") == []


async def test_filters_preferences_refresh(
    rt: Runtime, settings: Settings, queued: list[str]
) -> None:
    now = datetime.now(UTC)
    async with rt.sessionmaker.begin() as session:
        seco = NewsSource(
            kind="articles",
            name="Test SECO",
            url="https://a",
            feed_url="https://t.example/seco",
            country="CH",
            labour_market=True,
            fetched_at=now,
        )
        tech = NewsSource(
            kind="articles",
            name="Test tech",
            url="https://b",
            feed_url="https://t.example/tech",
            country="INT",
            language="en",
            fetched_at=now,
        )
        session.add_all([seco, tech])
        await session.flush()
        session.add_all(
            [
                NewsItem(
                    source_id=seco.id,
                    title="Chômage : 2,8 % en septembre",
                    url="https://t.example/1",
                    language="fr",
                    published_at=now,
                ),
                NewsItem(
                    source_id=tech.id,
                    title="Kubernetes 1.40 released",
                    url="https://t.example/2",
                    language="en",
                    published_at=now,
                ),
                NewsItem(
                    source_id=tech.id,
                    title="New phone review",
                    url="https://t.example/3",
                    language="en",
                    published_at=now,
                ),
            ]
        )
    await follow_test_sources(rt)
    app = create_app(settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        preferences = (await api.get("/api/news/preferences")).json()
        assert preferences["domain_only"] is False
        saved = await api.put(
            "/api/news/preferences",
            json={**preferences, "domain_keywords": ["kubernetes", "Kubernetes", " CKA "]},
        )
        assert saved.json()["domain_keywords"] == ["kubernetes", "CKA"]

        page = (await api.get("/api/news")).json()
        assert len(page["items"]) == 3 and page["fetched_at"] and not page["refreshing"]
        assert page["countries"] == ["CH", "INT"] and page["languages"] == ["en", "fr"]
        mine = (await api.get("/api/news", params={"domain_only": True})).json()["items"]
        # Le SECO reste (marché de l'emploi), l'article Kubernetes est trouvé et surligné.
        assert {i["title"] for i in mine} == {
            "Chômage : 2,8 % en septembre",
            "Kubernetes 1.40 released",
        }
        assert next(i for i in mine if i["title"].startswith("Kube"))["matched"] == ["kubernetes"]
        swiss = (await api.get("/api/news", params={"country": ["CH"]})).json()["items"]
        assert [i["source"] for i in swiss] == ["Test SECO"]
        french = (await api.get("/api/news", params={"language": ["fr"]})).json()["items"]
        assert [i["language"] for i in french] == ["fr"]

        changed = await api.patch(
            f"/api/news/sources/{tech.id}", json={"country": "", "labour_market": True}
        )
        updated = next(s for s in changed.json() if s["id"] == tech.id)
        assert updated["country"] is None and updated["labour_market"] and updated["active"]
        assert (await api.post("/api/news/refresh")).json() == {"queued": True}
        assert queued == ["news"]


async def test_first_visit_triggers_fetch(
    rt: Runtime, settings: Settings, queued: list[str]
) -> None:
    async with rt.sessionmaker.begin() as session:
        session.add(
            NewsSource(
                kind="articles", name="Test neuve", url="https://n", feed_url="https://t.example/n"
            )
        )
    await follow_test_sources(rt)
    app = create_app(settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        page = (await api.get("/api/news")).json()
    assert page["refreshing"] and page["fetched_at"] is None and queued == ["news"]


async def test_domain_suggested_from_offers(runtime: Runtime) -> None:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers CASCADE"))
    now = datetime.now(UTC)
    async with runtime.sessionmaker.begin() as session:
        offers = [
            Offer(fingerprint=f"o{n}", title=f"Poste {n}", first_seen_at=now, last_seen_at=now)
            for n in range(3)
        ]
        session.add_all(offers)
        await session.flush()
        keywords = [["DevOps", "Kubernetes"], ["devops", "AWS"], ["Comptabilité"]]
        scores = [85, 72, 30]  # la dernière, mal notée, ne compte pas
        session.add_all(
            Evaluation(
                offer_id=offer.id,
                filter_passed=True,
                criteria_hash="x",
                score=score,
                keywords_role=words,
            )
            for offer, words, score in zip(offers, keywords, scores, strict=True)
        )
    async with runtime.sessionmaker() as session:
        assert await domain.suggest(session) == ["DevOps", "Kubernetes", "AWS"]
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers CASCADE"))


def test_catalog_is_consistent() -> None:
    found = catalog.load()
    ids = [s.id for s in found.sources]
    feeds = [s.feed_url for s in found.sources]
    assert len(ids) == len(set(ids)) and len(feeds) == len(set(feeds))
    for source in found.sources:
        assert source.kind in ("articles", "videos")
        assert source.feed_url.startswith("https://") and source.url.startswith("https://")
        assert source.domains and set(source.domains) <= set(found.domains)
        assert source.country == "INT" or len(source.country) == 2
        assert source.description
    # Les sources de départ (migration 0023) y figurent, pour s'afficher « suivie ».
    assert {"seco", "rts-economie", "letemps-economie", "techworld-nana", "kodekloud"} <= set(ids)
    assert catalog.search_feed("Kubernetes emploi", "CH", "fr") == (
        "https://news.google.com/rss/search?q=Kubernetes+emploi&hl=fr&gl=CH&ceid=CH%3Afr"
    )
    assert "gl=US" in catalog.search_feed("CKA", "INT", "en")


async def test_catalog_and_searches_api(rt: Runtime, settings: Settings, queued: list[str]) -> None:
    app = create_app(settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        listed = (await api.get("/api/news/catalog")).json()
        assert listed["domains"]["devops"] == "DevOps et Kubernetes"
        by_id = {s["id"]: s for s in listed["sources"]}
        assert by_id["seco"]["added"] and not by_id["xavki"]["added"]
        added = await api.post("/api/news/catalog/xavki")
        assert added.status_code == 201 and queued == ["news"]
        xavki = next(s for s in added.json() if s["name"] == "xavki")
        assert (xavki["kind"], xavki["country"], xavki["language"]) == ("videos", "INT", "fr")
        assert (await api.post("/api/news/catalog/xavki")).status_code == 409
        assert (await api.post("/api/news/catalog/inconnue")).status_code == 404
        assert next(
            s for s in (await api.get("/api/news/catalog")).json()["sources"] if s["id"] == "xavki"
        )["added"]

        search = await api.post(
            "/api/news/searches",
            json={"query": "  Kubernetes   emploi ", "country": "CH", "language": "fr"},
        )
        assert search.status_code == 201
        veille = next(s for s in search.json() if s["query"])
        assert veille["name"] == "Veille : Kubernetes emploi" and veille["country"] == "CH"
        assert "q=Kubernetes+emploi" in veille["feed_url"]
        duplicate = await api.post(
            "/api/news/searches",
            json={"query": "Kubernetes emploi", "country": "CH", "language": "fr"},
        )
        assert duplicate.status_code == 409
        bad = await api.post(
            "/api/news/searches", json={"query": "x", "country": "CH", "language": "fr"}
        )
        assert bad.status_code == 422
    async with rt.engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM news_sources WHERE name IN ('xavki') OR query IS NOT NULL")
        )


async def test_search_items_cleaned_and_deduplicated(
    rt: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    google = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
<title>"CKA" - Google Actualités</title><language>fr</language>
<item><title>Le chômage reste à 3 % - Le Temps</title>
<link>https://news.google.com/rss/articles/abc?oc=5</link>
<pubDate>Tue, 06 Oct 2026 09:00:00 GMT</pubDate>
<source url="https://www.letemps.ch">Le Temps</source></item>
<item><title>Réussir la CKA en 30 jours - IT-Connect</title>
<link>https://news.google.com/rss/articles/def?oc=5</link>
<pubDate>Tue, 06 Oct 2026 09:00:00 GMT</pubDate>
<source url="https://www.it-connect.fr">IT-Connect</source></item>
</channel></rss>""".encode()

    async def fake_get(_client: Any, url: str, _limit: int) -> tuple[bytes, str]:
        if url.endswith("rss"):
            return RSS, url
        if "news.google.com" in url:
            return google, url
        raise logos.Refused("inconnu")

    monkeypatch.setattr(logos, "_get", fake_get)
    async with rt.sessionmaker.begin() as session:
        session.add_all(
            [
                NewsSource(
                    kind="articles",
                    name="Test RTS",
                    url="https://x",
                    feed_url="https://t.example/rss",
                ),
                NewsSource(
                    kind="articles",
                    name="Test veille",
                    url="https://news.google.com/",
                    feed_url=catalog.search_feed("CKA", "CH", "fr"),
                    query="CKA",
                ),
            ]
        )
    await follow_test_sources(rt)
    await news.fetch_news(rt)
    async with rt.sessionmaker() as session:
        rows = (
            await session.execute(
                select(NewsItem.title, NewsItem.summary, NewsSource.name).join(NewsSource)
            )
        ).all()
    found = {(title, name): summary for title, summary, name in rows}
    # Le même article, déjà relevé par la RTS, n'est pas repris par la veille.
    assert [name for title, name in found if title == "Le chômage reste à 3 %"] == ["Test RTS"]
    assert found[("Réussir la CKA en 30 jours", "Test veille")] == "IT-Connect"
