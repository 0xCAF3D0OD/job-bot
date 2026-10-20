"""Ajouter une offre trouvée ailleurs (docs/111) : un lien ou un texte devient une offre.

La lecture se fait dans l'ordre : le balisage `JobPosting` de la page (celui dont se nourrit
Google Jobs), sans IA ; sinon le texte de la page, ou le texte collé, lu par l'IA avec le
lecteur des alertes (docs/20), le nom de la personne retiré. Une page protégée contre les
robots n'est jamais contournée : on propose de coller le texte.
"""

import html
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import anthropic
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.filter import canton_of
from jobbot.core.normalize import normalize_offer, normalize_text, parse_rate
from jobbot.db.models import EnrichStatus, Offer, OfferLink, OfferStatus
from jobbot.filtering.service import run_filter
from jobbot.letters.service import load_identity
from jobbot.llm import alert as alert_llm
from jobbot.llm.client import Refused as LlmRefused
from jobbot.llm.proposals import scrub
from jobbot.llm.scoring import InvalidScore
from jobbot.log import get_logger
from jobbot.logos import service as logos
from jobbot.news import domain
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, budget_state, record_call

log = get_logger(__name__)

SOURCE = "manual"
MAX_PAGE_BYTES = 2_000_000
TIMEOUT_SECONDS = 10
DAILY_LIMIT = 20
MAX_TEXT = 20_000
READ_ESTIMATE_USD = Decimal("0.02")
# Le lecteur d'alertes rattache chaque offre à un lien : un texte collé sans lien en reçoit un.
NO_LINK = "https://annonce-collee.invalid/"
_LD_JSON = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)


class ReadProblem(Exception):
    """Ce qui empêche de lire l'annonce ; `paste` : proposer de coller son texte."""

    def __init__(self, message: str, *, paste: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.paste = paste


@dataclass
class Draft:
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
    # « page » : lue dans le balisage de la page ; « ia » : lue par l'IA.
    read_by: str = "page"
    # Cohérence avec le poste (docs/111) : les mots du métier trouvés dans l'annonce.
    trade: str | None = None
    matches_trade: bool = True
    existing_offer_id: int | None = None


# --- Le balisage JobPosting -------------------------------------------------------------


def _types(item: dict[str, Any]) -> list[str]:
    value = item.get("@type")
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


def job_posting(page: str) -> dict[str, Any] | None:
    """Le premier `JobPosting` des blocs JSON-LD, y compris dans un `@graph` ou une liste."""
    for match in _LD_JSON.finditer(page):
        try:
            data = json.loads(html.unescape(match.group(1)).strip())
        except json.JSONDecodeError:
            continue
        stack: list[Any] = [data]
        while stack:
            item = stack.pop(0)
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                if "JobPosting" in _types(item):
                    return item
                if isinstance(item.get("@graph"), list):
                    stack.extend(item["@graph"])
    return None


def _text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    soup = BeautifulSoup(html.unescape(value), "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    lines = [" ".join(line.split()) for line in soup.get_text("\n").splitlines()]
    return "\n".join(line for line in lines if line) or None


def _location(posting: dict[str, Any]) -> str | None:
    places = posting.get("jobLocation")
    place = places[0] if isinstance(places, list) and places else places
    address = place.get("address") if isinstance(place, dict) else None
    if isinstance(address, dict):
        town = address.get("addressLocality") or address.get("addressRegion")
        if town:
            return " ".join(str(town).split())
    if str(posting.get("jobLocationType", "")).upper() == "TELECOMMUTE":
        return "Télétravail"
    return None


def draft_from_posting(posting: dict[str, Any], url: str) -> Draft | None:
    title = _text(posting.get("title") or posting.get("name"))
    if not title:
        return None
    org = posting.get("hiringOrganization")
    company = org.get("name") if isinstance(org, dict) else org if isinstance(org, str) else None
    description = _text(posting.get("description"))
    return Draft(
        title=title.splitlines()[0][:300],
        company=" ".join(str(company).split())[:300] if company else None,
        location=_location(posting),
        description=description[:MAX_TEXT] if description else None,
        url=url,
        read_by="page",
    )


# --- Lire une page, ou un texte par l'IA ------------------------------------------------


async def fetch_page(url: str) -> str:
    """La page publique de l'annonce, une fois : https, jamais une adresse privée, 2 Mo et
    10 secondes au plus (les règles des logos, docs/exploitation)."""
    async with httpx.AsyncClient(
        timeout=TIMEOUT_SECONDS, follow_redirects=False, headers={"User-Agent": logos.USER_AGENT}
    ) as client:
        try:
            data, _final = await logos._get(client, url, MAX_PAGE_BYTES)
        except logos.Refused as exc:
            raise ReadProblem(f"Lien refusé : {exc}.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403, 429):
                raise ReadProblem(
                    "Ce site ne se laisse pas lire par un robot : colle le texte de l'annonce.",
                    paste=True,
                ) from exc
            code = exc.response.status_code
            raise ReadProblem(
                f"La page ne répond pas ({code}) : colle le texte de l'annonce.", paste=True
            ) from exc
        except httpx.HTTPError as exc:
            raise ReadProblem(
                "La page ne répond pas : colle le texte de l'annonce.", paste=True
            ) from exc
    return data.decode("utf-8", errors="replace")


def page_text(page: str) -> str:
    soup = BeautifulSoup(page, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


async def read_with_ai(runtime: Runtime, text: str, url: str | None) -> Draft:
    """Le texte de l'annonce lu par l'IA (lecteur des alertes), le nom de la personne retiré."""
    settings = runtime.settings
    if not settings.llm_configured:
        raise ReadProblem("L'IA n'est pas configurée : remplis la fiche à la main.")
    now = datetime.now(UTC)
    async with runtime.sessionmaker() as session:
        spend, budget, rate = await budget_state(session, now)
        identity = await load_identity(session)
    if spend + READ_ESTIMATE_USD * rate > budget:
        raise ReadProblem("Plafond de l'IA atteint ce mois : remplis la fiche à la main.")
    clean = " ".join(text.split())
    for name in (identity.name or "").split():
        if len(name) > 2:
            clean = re.sub(re.escape(name), "[nom retiré]", clean, flags=re.IGNORECASE)
    prepared = alert_llm.AlertInput(text=scrub(clean)[:MAX_TEXT], links=[url or NO_LINK])
    client = scoring_service.make_client(settings)
    try:
        raw = await client.score(alert_llm.request_params(prepared, "Annonce ajoutée"))
    except LlmRefused as exc:
        raise ReadProblem("L'IA n'a pas voulu lire ce texte : remplis la fiche à la main.") from exc
    except anthropic.APIStatusError as exc:
        problem = account_problem(exc) or f"API ({exc.status_code})"
        raise ReadProblem(f"L'IA ne répond pas ({problem}) : réessaie dans un moment.") from exc
    except anthropic.APIConnectionError as exc:
        raise ReadProblem("L'IA est injoignable : réessaie dans un moment.") from exc
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=None, rate=rate, purpose="manual_offer")
    try:
        alert = alert_llm.parse_output(raw.text, prepared, None)
    except InvalidScore as exc:
        raise ReadProblem("L'annonce n'a pas pu être lue : remplis la fiche à la main.") from exc
    if not alert.offers:
        raise ReadProblem("Je ne trouve pas d'annonce dans ce texte : remplis la fiche à la main.")
    first = alert.offers[0]
    return Draft(
        title=first.title,
        company=first.company,
        location=first.location,
        description=clean[:MAX_TEXT],
        url=url,
        read_by="ia",
    )


async def trade(session: AsyncSession) -> tuple[str | None, list[str]]:
    """Le métier (premier mot de « Mon domaine », posé par l'accueil) et tous les mots."""
    words = [w.strip() for w in await domain.keywords(session) if w.strip()]
    return (words[0] if words else None), words


def about_trade(words: list[str], *texts: str | None) -> bool:
    """L'annonce parle-t-elle du métier ? Un mot-clé entier, ou le début (5 lettres) d'un de
    ses mots : « développeur » reconnaît « développeuse », « Entwickler » « Entwicklerin »."""
    if domain.matched(words, *texts):
        return True
    haystack = f" {normalize_text(' '.join(t for t in texts if t))}"
    stems = {w[:5] for k in words for w in normalize_text(k).split() if len(w) >= 4}
    return any(f" {stem}" in haystack for stem in stems)


async def _complete(session: AsyncSession, draft: Draft) -> Draft:
    """La cohérence avec le poste et une offre déjà là (même lien, ou même titre et entreprise)."""
    draft.trade, words = await trade(session)
    if words:
        draft.matches_trade = about_trade(words, draft.title, draft.description)
    norm = normalize_offer(draft.title, draft.company, draft.location)
    existing = await session.scalar(select(Offer.id).where(Offer.fingerprint == norm.fingerprint))
    if existing is None and draft.url:
        existing = await session.scalar(
            select(OfferLink.offer_id).where(OfferLink.url == draft.url).limit(1)
        )
    draft.existing_offer_id = existing
    return draft


async def read(runtime: Runtime, url: str | None, text: str | None) -> Draft:
    """La fiche de l'annonce, à relire avant de l'ajouter."""
    if url:
        page = await fetch_page(url)
        posting = job_posting(page)
        draft = draft_from_posting(posting, url) if posting else None
        if draft is None:
            body = page_text(page)
            if len(body) < 200:
                raise ReadProblem(
                    "Cette page ne montre pas d'annonce lisible : colle le texte de l'annonce.",
                    paste=True,
                )
            draft = await read_with_ai(runtime, body, url)
    elif text and text.strip():
        draft = await read_with_ai(runtime, text, None)
    else:
        raise ReadProblem("Colle le lien ou le texte de l'annonce.")
    async with runtime.sessionmaker() as session:
        return await _complete(session, draft)


# --- Ajouter ----------------------------------------------------------------------------


async def added_today(session: AsyncSession) -> int:
    since = datetime.now(UTC) - timedelta(days=1)
    count = await session.scalar(
        select(func.count(func.distinct(OfferLink.offer_id)))
        .join(Offer, Offer.id == OfferLink.offer_id)
        .where(OfferLink.source == SOURCE, Offer.first_seen_at >= since)
    )
    return int(count or 0)


async def add(runtime: Runtime, draft: Draft) -> int:
    """L'offre ajoutée, puis le filtre (la note suit au prochain passage du worker). Une offre
    écartée par les critères est gardée : c'est ton choix, la raison s'affiche (docs/111)."""
    now = datetime.now(UTC)
    norm = normalize_offer(draft.title, draft.company, draft.location)
    rate_min, rate_max = norm.rate_min, norm.rate_max
    if rate_min is None and draft.location:
        rate_min, rate_max = parse_rate(draft.location)
    async with runtime.sessionmaker.begin() as session:
        existing = await session.scalar(
            select(Offer.id).where(Offer.fingerprint == norm.fingerprint)
        )
        if existing is not None:
            return int(existing)
        if await added_today(session) >= DAILY_LIMIT:
            raise ReadProblem(f"{DAILY_LIMIT} offres ajoutées en 24 heures : c'est le maximum.")
        offer = Offer(
            fingerprint=norm.fingerprint,
            title=draft.title.strip()[:300],
            company=(draft.company or "").strip()[:300] or None,
            location=(draft.location or "").strip()[:300] or None,
            rate_min=rate_min,
            rate_max=rate_max,
            canton=canton_of(draft.location),
            snippet=(draft.description or "")[:500] or None,
            description=draft.description,
            status=OfferStatus.NEW,
            first_seen_at=now,
            seen_since=now,
            last_seen_at=now,
            enrich_status=EnrichStatus.SKIPPED,
        )
        session.add(offer)
        await session.flush()
        session.add(
            OfferLink(offer_id=offer.id, source=SOURCE, external_id=None, url=draft.url or "")
        )
        offer_id = offer.id
    await run_filter(runtime)
    log.info("manual_offer_added", offer=offer_id, read_by=draft.read_by)
    return int(offer_id)
