"""Actualités (docs/15 §2) : relevé des flux toutes les 6 heures, miniatures, nettoyage.

Les requêtes passent par les mêmes garde-fous que les logos (https, pas d'adresse interne,
taille limitée). Les miniatures sont téléchargées et servies par la plateforme.
"""

import hashlib
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from jobbot.db.models import NewsItem, NewsSource
from jobbot.log import get_logger
from jobbot.logos import service as logos
from jobbot.news import language
from jobbot.news.feeds import Feed, FeedError, FeedItem, parse_feed
from jobbot.runtime import Runtime

log = get_logger(__name__)

MAX_FEED_BYTES = 3_000_000
MAX_PAGE_BYTES = 1_500_000
MAX_IMAGE_BYTES = 300_000
MAX_ITEMS_PER_SOURCE = 30
KEEP_FOR = timedelta(days=60)
USER_AGENT = "job-bot/0.8 (usage personnel)"
_YOUTUBE_ID = re.compile(r"(UC[\w-]{22})")
_YOUTUBE_CHANNEL_URL = re.compile(
    r"https://(?:www\.|m\.)?youtube\.com/channel/(UC[\w-]{22})(?:[/?#]|$)"
)
_YOUTUBE_CHANNEL = re.compile(
    r'"(?:externalId|channelId)":"(UC[\w-]{20,})"|channel_id=(UC[\w-]{20,})'
)


class SourceError(ValueError):
    """Adresse sans flux lisible."""


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15, follow_redirects=False, headers={"User-Agent": USER_AGENT})


@dataclass(frozen=True)
class ResolvedSource:
    kind: str
    name: str
    url: str
    feed_url: str
    # Proposés à l'ajout, modifiables ensuite (docs/16 §3).
    country: str | None = None
    language: str | None = None


_COUNTRY_TLD = {"ch": "CH", "fr": "FR", "be": "BE", "ca": "CA", "lu": "LU", "de": "DE", "at": "AT"}


def guess_country(url: str) -> str:
    """Pays d'après le domaine (.ch → CH) ; international pour YouTube et les .com."""
    host = urlsplit(url).hostname or ""
    return _COUNTRY_TLD.get(host.rsplit(".", 1)[-1], "INT")


def feed_language(feed: Feed) -> str | None:
    """Langue déclarée par le flux, sinon celle de la majorité de ses contenus."""
    declared = language.from_feed(feed.language)
    if declared:
        return declared
    found = [language.detect(f"{i.title} {i.summary or ''}") for i in feed.items[:20]]
    counts = Counter(lang for lang in found if lang)
    if not counts:
        return None
    best, count = counts.most_common(1)[0]
    return best if count * 2 > len([f for f in found if f]) else None


def item_language(item: FeedItem, fallback: str | None) -> str | None:
    return language.detect(f"{item.title} {item.summary or ''}") or fallback


async def resolve(url: str) -> ResolvedSource:
    """Adresse d'un site, d'un flux ou d'une chaîne YouTube → flux et nom."""
    url = url.strip()
    # ID de chaîne YouTube, seul ou dans une adresse /channel/ : flux connu, sans lire de page.
    given = _YOUTUBE_ID.fullmatch(url) or _YOUTUBE_CHANNEL_URL.match(url)
    if given:
        url = f"https://www.youtube.com/channel/{given.group(1)}"
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={given.group(1)}"
        async with _client() as client:
            try:
                feed_data, _ = await logos._get(client, feed_url, MAX_FEED_BYTES)
                feed = parse_feed(feed_data)
            except (logos.Refused, httpx.HTTPError, FeedError):
                raise SourceError("chaîne YouTube introuvable") from None
        return ResolvedSource(
            "videos", feed.title or "YouTube", url, feed_url, "INT", feed_language(feed)
        )
    if not url.startswith("https://"):
        raise SourceError("adresse en https:// attendue")
    host = urlsplit(url).hostname or ""
    async with _client() as client:
        try:
            data, final = await logos._get(client, url, MAX_PAGE_BYTES)
        except (logos.Refused, httpx.HTTPError) as exc:
            raise SourceError(f"adresse injoignable ({exc})") from None
        # Déjà un flux ?
        try:
            feed = parse_feed(data)
            kind = "videos" if "youtube.com" in host else "articles"
            return ResolvedSource(
                kind, feed.title or host, url, url, guess_country(url), feed_language(feed)
            )
        except FeedError:
            pass
        text = data.decode("utf-8", errors="replace")
        if host.endswith("youtube.com"):
            match = _YOUTUBE_CHANNEL.search(text)
            if not match:
                # Page de consentement aux cookies (Europe) : on ne l'accepte pas à ta place.
                raise SourceError(
                    "YouTube ne montre pas cette page sans consentement aux cookies ; "
                    "colle l'ID de la chaîne (sur la chaîne : « … plus » → "
                    "« Partager la chaîne » → « Copier l'ID de la chaîne »)"
                )
            channel = match.group(1) or match.group(2)
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
            kind = "videos"
        else:
            soup = BeautifulSoup(text, "html.parser")
            link = soup.find(
                "link", attrs={"type": re.compile(r"application/(rss|atom)\+xml"), "href": True}
            )
            if link is None:
                raise SourceError("aucun flux RSS annoncé par cette page")
            feed_url = urljoin(final, str(link["href"]))
            kind = "articles"
        try:
            feed_data, _ = await logos._get(client, feed_url, MAX_FEED_BYTES)
            feed = parse_feed(feed_data)
        except (logos.Refused, httpx.HTTPError, FeedError) as exc:
            raise SourceError(f"flux illisible ({exc})") from None
    return ResolvedSource(
        kind, feed.title or host, url, feed_url, guess_country(url), feed_language(feed)
    )


@dataclass
class NewsResult:
    sources: int = 0
    new_items: int = 0
    failed: int = 0


def _matches(source: NewsSource, title: str, summary: str | None, author: str | None) -> bool:
    if not source.match:
        return True
    needle = source.match.casefold()
    return any(needle in (value or "").casefold() for value in (author, title, summary))


async def _thumbnail(runtime: Runtime, client: httpx.AsyncClient, url: str) -> str | None:
    try:
        data, _ = await logos._get(client, url, MAX_IMAGE_BYTES)
    except (logos.Refused, httpx.HTTPError):
        return None
    media_type = logos.sniff(data)
    if media_type is None or media_type == "image/svg+xml":
        return None
    extension = media_type.rsplit("/", 1)[1].replace("x-icon", "ico")
    key = f"news/{hashlib.sha256(url.encode()).hexdigest()[:24]}.{extension}"
    runtime.storage.put(key, data)
    return key


async def fetch_news(runtime: Runtime) -> NewsResult:
    result = NewsResult()
    now = datetime.now(UTC)
    async with runtime.sessionmaker() as session:
        sources = list(await session.scalars(select(NewsSource).where(NewsSource.active.is_(True))))
    async with _client() as client:
        for source in sources:
            result.sources += 1
            try:
                data, _ = await logos._get(client, source.feed_url, MAX_FEED_BYTES)
                feed: Feed = parse_feed(data, now)
            except (logos.Refused, httpx.HTTPError, FeedError) as exc:
                result.failed += 1
                async with runtime.sessionmaker.begin() as session:
                    await session.execute(
                        update(NewsSource)
                        .where(NewsSource.id == source.id)
                        .values(fetched_at=now, error=str(exc)[:300] or type(exc).__name__)
                    )
                continue
            fallback = language.from_feed(feed.language) or source.language
            entries = [i for i in feed.items if _matches(source, i.title, i.summary, i.author)][
                :MAX_ITEMS_PER_SOURCE
            ]
            async with runtime.sessionmaker() as session:
                known = set(
                    await session.scalars(
                        select(NewsItem.url).where(NewsItem.url.in_([i.url for i in entries]))
                    )
                )
            for item in entries:
                if item.url in known or item.published_at < now - KEEP_FOR:
                    continue
                image_key = (
                    await _thumbnail(runtime, client, item.image_url) if item.image_url else None
                )
                async with runtime.sessionmaker.begin() as session:
                    inserted = await session.scalar(
                        insert(NewsItem)
                        .values(
                            source_id=source.id,
                            title=item.title[:300],
                            url=item.url,
                            summary=item.summary,
                            image_url=item.image_url,
                            image_key=image_key,
                            language=item_language(item, fallback),
                            published_at=min(item.published_at, now),
                        )
                        .on_conflict_do_nothing(index_elements=["url"])
                        .returning(NewsItem.id)
                    )
                result.new_items += inserted is not None
            async with runtime.sessionmaker.begin() as session:
                await session.execute(
                    update(NewsSource)
                    .where(NewsSource.id == source.id)
                    .values(fetched_at=now, error=None)
                )
    await purge(runtime, now)
    await _backfill_languages(runtime)
    log.info("news_finished", sources=result.sources, new=result.new_items, failed=result.failed)
    return result


async def purge(runtime: Runtime, now: datetime) -> None:
    async with runtime.sessionmaker.begin() as session:
        old = list(
            await session.scalars(
                select(NewsItem.image_key).where(
                    NewsItem.published_at < now - KEEP_FOR, NewsItem.image_key.is_not(None)
                )
            )
        )
        await session.execute(delete(NewsItem).where(NewsItem.published_at < now - KEEP_FOR))
    for key in old:
        if key:
            runtime.storage.delete(key)


async def _backfill_languages(runtime: Runtime) -> None:
    """Contenus relevés avant la 0.9 : langue déduite du texte, sinon celle de la source."""
    async with runtime.sessionmaker.begin() as session:
        rows = (
            await session.execute(
                select(NewsItem, NewsSource.language)
                .join(NewsSource, NewsSource.id == NewsItem.source_id)
                .where(NewsItem.language.is_(None))
                .limit(2000)
            )
        ).all()
        for item, fallback in rows:
            item.language = language.detect(f"{item.title} {item.summary or ''}") or fallback
