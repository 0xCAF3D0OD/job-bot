"""Lecture des flux RSS 2.0 et Atom (dont les chaînes YouTube), sans dépendance externe.

Un flux est une donnée venue d'Internet : les déclarations d'entités XML sont refusées
(pas d'expansion), le texte est débarrassé de son HTML et tronqué.
"""

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

MAX_SUMMARY = 280
_TAG = re.compile(r"<[^>]+>")
_IMG = re.compile(r"""<img[^>]+src=["'](https://[^"']+)["']""", re.I)


class FeedError(ValueError):
    pass


@dataclass(frozen=True)
class FeedItem:
    title: str
    url: str
    summary: str | None
    image_url: str | None
    published_at: datetime
    author: str | None


@dataclass(frozen=True)
class Feed:
    title: str | None
    items: list[FeedItem]
    # Langue déclarée par le flux (<language> en RSS, xml:lang en Atom), telle quelle.
    language: str | None = None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(element: ET.Element, name: str) -> ET.Element | None:
    return next((c for c in element if _local(c.tag) == name), None)


def _text(element: ET.Element | None) -> str:
    return "".join(element.itertext()).strip() if element is not None else ""


def clean(value: str | None) -> str | None:
    """Texte brut : sans balises ni entités, espaces réduits, 280 caractères au plus."""
    if not value:
        return None
    text = " ".join(html.unescape(_TAG.sub(" ", value)).split())
    if len(text) > MAX_SUMMARY:
        text = text[: MAX_SUMMARY - 1].rsplit(" ", 1)[0] + "…"
    return text or None


def _date(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)  # RSS : « Mon, 06 Oct 2026 08:00:00 +0200 »
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))  # Atom, ou « 2026-10-06 »
        except ValueError:
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def parse_feed(data: bytes, now: datetime | None = None) -> Feed:
    if b"<!ENTITY" in data[:5000].upper():
        raise FeedError("flux refusé : déclaration d'entités XML")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise FeedError(f"flux illisible : {exc}") from exc
    now = now or datetime.now(UTC)
    items: list[FeedItem] = []
    if _local(root.tag) == "rss":
        channel = _child(root, "channel")
        if channel is None:
            raise FeedError("flux RSS sans canal")
        title = _text(_child(channel, "title")) or None
        language = _text(_child(channel, "language")) or None
        for entry in (c for c in channel if _local(c.tag) == "item"):
            link = _text(_child(entry, "link"))
            description = _text(_child(entry, "description"))
            enclosure = _child(entry, "enclosure")
            media = next(
                (
                    c
                    for c in entry.iter()
                    if _local(c.tag) in ("thumbnail", "content") and c.get("url")
                ),
                None,
            )
            image = (
                (
                    enclosure.get("url")
                    if enclosure is not None and (enclosure.get("type") or "").startswith("image/")
                    else None
                )
                or (media.get("url") if media is not None else None)
                or (m.group(1) if (m := _IMG.search(description)) else None)
            )
            items.append(
                FeedItem(
                    title=clean(_text(_child(entry, "title"))) or "",
                    url=link,
                    summary=clean(description),
                    image_url=image,
                    published_at=_date(_text(_child(entry, "pubDate"))) or now,
                    author=_text(_child(entry, "author"))
                    or _text(_child(entry, "creator"))
                    or _text(_child(entry, "source"))  # Google Actualités : le journal
                    or None,
                )
            )
    elif _local(root.tag) == "RDF":
        # RSS 1.0 : les articles sont à côté du canal, la date en dc:date.
        channel = _child(root, "channel")
        title = _text(_child(channel, "title")) if channel is not None else None
        language = _text(_child(channel, "language")) if channel is not None else None
        for entry in (c for c in root if _local(c.tag) == "item"):
            description = _text(_child(entry, "description"))
            items.append(
                FeedItem(
                    title=clean(_text(_child(entry, "title"))) or "",
                    url=_text(_child(entry, "link")),
                    summary=clean(description),
                    image_url=m.group(1) if (m := _IMG.search(description)) else None,
                    published_at=_date(_text(_child(entry, "date"))) or now,
                    author=_text(_child(entry, "creator")) or None,
                )
            )
    elif _local(root.tag) == "feed":
        title = _text(_child(root, "title")) or None
        language = root.get("{http://www.w3.org/XML/1998/namespace}lang")
        for entry in (c for c in root if _local(c.tag) == "entry"):
            link_el = next(
                (
                    c
                    for c in entry
                    if _local(c.tag) == "link" and c.get("rel", "alternate") == "alternate"
                ),
                None,
            )
            group = _child(entry, "group")  # YouTube : media:group
            thumbnail = next((c for c in entry.iter() if _local(c.tag) == "thumbnail"), None)
            summary = _text(_child(entry, "summary")) or _text(_child(entry, "content"))
            if not summary and group is not None:
                summary = _text(_child(group, "description"))
            author = _child(entry, "author")
            items.append(
                FeedItem(
                    title=clean(_text(_child(entry, "title"))) or "",
                    url=(link_el.get("href") or "") if link_el is not None else "",
                    summary=clean(summary),
                    image_url=thumbnail.get("url") if thumbnail is not None else None,
                    published_at=_date(
                        _text(_child(entry, "published")) or _text(_child(entry, "updated"))
                    )
                    or now,
                    author=_text(_child(author, "name")) if author is not None else None,
                )
            )
    else:
        raise FeedError("ni RSS ni Atom")
    kept = [i for i in items if i.title and i.url.startswith(("https://", "http://"))]
    return Feed(title=clean(title), items=kept, language=language)
