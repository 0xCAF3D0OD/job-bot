"""Logos des entreprises, téléchargés une fois et servis par la plateforme (docs/14 §4).

Sources : logo relevé sur la page de l'offre ou dans l'e-mail d'alerte, sinon icône du site
de l'entreprise. Le navigateur de Kevin n'appelle jamais ces sites : seul le serveur le fait,
une fois par entreprise, avec des garde-fous (https, pas d'adresse interne, 200 Ko au plus,
formats d'image vérifiés, SVG sans script).
"""

import asyncio
import hashlib
import ipaddress
import re
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from jobbot.db.models import Company, CompanyLogo, Offer, OfferStatus
from jobbot.log import get_logger
from jobbot.registry.service import name_key
from jobbot.runtime import Runtime

log = get_logger(__name__)

MAX_BYTES = 200_000
MAX_PAGE_BYTES = 400_000
MAX_PER_RUN = 25
DELAY_SECONDS = 2.0
RETRY_AFTER = timedelta(days=30)
USER_AGENT = "job-bot/0.7 (usage personnel)"
WATCHED = (
    OfferStatus.NEW,
    OfferStatus.TO_REVIEW,
    OfferStatus.LATER,
    OfferStatus.PREPARING,
    OfferStatus.APPLIED,
)
_SVG_DANGER = re.compile(
    r"<script|<foreignobject|javascript:|\son\w+\s*=|href\s*=\s*[\"']?(?:https?:|//)", re.I
)

sleep: Callable[[float], Awaitable[None]] = asyncio.sleep


class Refused(Exception):
    """Adresse ou contenu refusé par les garde-fous."""


def sniff(data: bytes) -> str | None:
    """Type d'image d'après les premiers octets ; None si ce n'est pas une image acceptée."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:4] == b"\x00\x00\x01\x00":
        return "image/x-icon"
    head = data[:1000].lstrip().lower()
    if head.startswith((b"<svg", b"<?xml")) and b"<svg" in data[:4000].lower():
        text = data.decode("utf-8", errors="replace")
        return None if _SVG_DANGER.search(text) else "image/svg+xml"
    return None


async def _check_host(url: str) -> None:
    """https seulement, et jamais une adresse privée, locale ou réservée (même après DNS)."""
    parts = urlsplit(url)
    host = parts.hostname or ""
    if (
        parts.scheme != "https"
        or not host
        or host == "localhost"
        or host.endswith((".local", ".internal"))
    ):
        raise Refused(f"adresse refusée : {host or url[:40]}")
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise Refused(f"nom introuvable : {host}") from exc
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global:
            raise Refused(f"adresse non publique : {host}")


async def _get(client: httpx.AsyncClient, url: str, limit: int) -> tuple[bytes, str]:
    """Contenu (tronqué au-delà de la limite : refusé) et adresse finale après redirections."""
    current = url
    for _ in range(4):
        await _check_host(current)
        async with client.stream("GET", current) as response:
            if response.is_redirect and response.headers.get("location"):
                current = urljoin(current, response.headers["location"])
                continue
            response.raise_for_status()
            data = b""
            async for chunk in response.aiter_bytes():
                data += chunk
                if len(data) > limit:
                    raise Refused("fichier trop lourd")
            return data, current
    raise Refused("trop de redirections")


async def _site_icon(client: httpx.AsyncClient, website: str) -> str | None:
    """Icône déclarée par la page d'accueil (la plus grande), sinon /favicon.ico."""
    parts = urlsplit(website)
    home = f"https://{parts.hostname}/"
    try:
        page, final = await _get(client, home, MAX_PAGE_BYTES)
    except (Refused, httpx.HTTPError):
        return urljoin(home, "/favicon.ico")
    soup = BeautifulSoup(page, "html.parser")
    best: tuple[int, str] | None = None
    for link in soup.find_all("link", href=True):
        rel = " ".join(link.get("rel") or []).lower()
        if "icon" not in rel:
            continue
        sizes = str(link.get("sizes") or "")
        size = max(
            (int(n) for n in re.findall(r"(\d+)x\d+", sizes)), default=180 if "apple" in rel else 32
        )
        if best is None or size > best[0]:
            best = (size, urljoin(final, str(link["href"])))
    return best[1] if best else urljoin(final, "/favicon.ico")


@dataclass
class LogoResult:
    examined: int = 0
    found: int = 0
    missing: int = 0


async def download(client: httpx.AsyncClient, url: str) -> tuple[bytes, str]:
    data, _ = await _get(client, url, MAX_BYTES)
    media_type = sniff(data)
    if media_type is None:
        raise Refused("pas une image acceptée")
    return data, media_type


async def fetch_logos(runtime: Runtime) -> LogoResult:
    """Télécharge le logo des entreprises des offres utiles qui n'en ont pas encore."""
    result = LogoResult()
    now = datetime.now(UTC)
    async with runtime.sessionmaker() as session:
        rows = (
            await session.execute(
                select(
                    Offer.company, Offer.logo_url, Offer.company_website, Offer.company_address_url
                )
                .where(Offer.company.is_not(None), Offer.status.in_(WATCHED))
                .order_by(Offer.first_seen_at.desc())
            )
        ).all()
        done = {
            key
            for key in await session.scalars(
                select(CompanyLogo.name_key).where(CompanyLogo.checked_at > now - RETRY_AFTER)
            )
        }
        websites = {
            key: url
            for key, url in (
                await session.execute(
                    select(Company.name_key, Company.source_url).where(
                        Company.source_url.is_not(None)
                    )
                )
            ).all()
        }
    # Par entreprise : un logo relevé (page, e-mail), sinon le site connu.
    todo: dict[str, dict[str, str | None]] = {}
    for company, logo_url, website, address_url in rows:
        key = name_key(company or "")
        if not key or key in done:
            continue
        entry = todo.setdefault(key, {"logo": None, "website": None})
        entry["logo"] = entry["logo"] or logo_url
        entry["website"] = entry["website"] or website or address_url or websites.get(key)

    async with httpx.AsyncClient(
        timeout=10, follow_redirects=False, headers={"User-Agent": USER_AGENT}
    ) as client:
        for index, (key, entry) in enumerate(list(todo.items())[:MAX_PER_RUN]):
            if index:
                await sleep(DELAY_SECONDS)
            result.examined += 1
            candidates: list[tuple[str, str]] = []
            if entry["logo"]:
                candidates.append((entry["logo"], "page"))
            if entry["website"]:
                icon = await _site_icon(client, entry["website"])
                if icon:
                    candidates.append((icon, "site"))
            stored: tuple[str, str, str] | None = None
            for url, source in candidates:
                try:
                    data, media_type = await download(client, url)
                except (Refused, httpx.HTTPError) as exc:
                    log.info("logo_refused", reason=str(exc)[:80] or type(exc).__name__)
                    continue
                extension = (
                    media_type.rsplit("/", 1)[1].replace("svg+xml", "svg").replace("x-icon", "ico")
                )
                storage_key = f"logos/{hashlib.sha256(key.encode()).hexdigest()[:20]}.{extension}"
                runtime.storage.put(storage_key, data)
                if source == "page" and "jobup" not in (urlsplit(url).hostname or ""):
                    source = "email"  # relevé dans une alerte (LinkedIn, jobs.ch…)
                stored = (storage_key, media_type, source)
                break
            values = {
                "storage_key": stored[0] if stored else None,
                "media_type": stored[1] if stored else None,
                "source": stored[2] if stored else None,
                "checked_at": now,
            }
            async with runtime.sessionmaker.begin() as session:
                await session.execute(
                    insert(CompanyLogo)
                    .values(name_key=key, **values)
                    .on_conflict_do_update(index_elements=["name_key"], set_=values)
                )
            if stored:
                result.found += 1
            else:
                result.missing += 1
    log.info("logos_finished", examined=result.examined, found=result.found, missing=result.missing)
    return result
