"""Ajouter une offre trouvée ailleurs (docs/111) : un lien ou un texte devient une offre.

La lecture se fait dans l'ordre : le balisage `JobPosting` de la page (celui dont se nourrit
Google Jobs), sans IA ; sinon le texte de la page, ou le texte collé, lu par l'IA avec le
lecteur des alertes (docs/20), le nom de la personne retiré. Une page protégée contre les
robots n'est jamais contournée : on propose de coller le texte.
"""

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import anthropic
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.filter import canton_of
from jobbot.core.normalize import (
    NormalizedOffer,
    normalize_company,
    normalize_offer,
    normalize_text,
    normalize_title,
    parse_rate,
)
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
from jobbot.sources import jobposting

log = get_logger(__name__)

SOURCE = "manual"
MAX_PAGE_BYTES = 2_000_000
TIMEOUT_SECONDS = 10
DAILY_LIMIT = 20
MAX_TEXT = 20_000
READ_ESTIMATE_USD = Decimal("0.02")
# Le lecteur d'alertes rattache chaque offre à un lien : un texte collé sans lien en reçoit un.
NO_LINK = "https://annonce-collee.invalid/"


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
    # Ce que l'annonce peut apporter à l'offre déjà là : ses champs vides (docs/111).
    fillable: list[str] = field(default_factory=list)


# --- Le balisage JobPosting -------------------------------------------------------------


job_posting = jobposting.job_posting


def draft_from_posting(posting: dict[str, Any], url: str) -> Draft | None:
    title = jobposting.text(posting.get("title") or posting.get("name"))
    if not title:
        return None
    org = posting.get("hiringOrganization")
    company = org.get("name") if isinstance(org, dict) else org if isinstance(org, str) else None
    description = jobposting.text(posting.get("description"))
    return Draft(
        title=title.splitlines()[0][:300],
        company=" ".join(str(company).split())[:300] if company else None,
        location=jobposting.location(posting),
        description=description[:MAX_TEXT] if description else None,
        url=url,
        read_by="page",
    )


# --- Lire une page, ou un texte par l'IA ------------------------------------------------


# Remplaçable en test (pas de réseau).
TRANSPORT: httpx.AsyncBaseTransport | None = None


async def fetch_page(url: str, before: Callable[[str], Awaitable[None]] | None = None) -> str:
    """La page publique de l'annonce, une fois : https, jamais une adresse privée, 2 Mo et
    10 secondes au plus (les règles des logos, docs/exploitation). `before` : appelé avant
    chaque requête, redirections comprises."""
    async with httpx.AsyncClient(
        timeout=TIMEOUT_SECONDS,
        follow_redirects=False,
        headers={"User-Agent": logos.USER_AGENT},
        transport=TRANSPORT,
    ) as client:
        try:
            data, _final = await logos._get(client, url, MAX_PAGE_BYTES, before)
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
    existing = await same_offer(session, norm)
    if existing is None and draft.url:
        existing = await session.scalar(
            select(OfferLink.offer_id).where(OfferLink.url == draft.url).limit(1)
        )
    draft.existing_offer_id = existing
    draft.fillable = await _fillable(session, existing, draft) if existing is not None else []
    return draft


async def same_offer(session: AsyncSession, norm: NormalizedOffer) -> int | None:
    """L'offre déjà là : même empreinte, ou même poste chez la même entreprise ailleurs
    (une offre de LinkedIn sans lieu, la même sur la page de l'employeur avec son lieu)."""
    existing = await session.scalar(select(Offer.id).where(Offer.fingerprint == norm.fingerprint))
    if existing is not None or not norm.company_key:
        return existing
    rows = await session.execute(
        select(Offer.id, Offer.title, Offer.company)
        .where(Offer.company.is_not(None), Offer.spontaneous.is_(False))
        .order_by(Offer.first_seen_at.desc())
    )
    for offer_id, title, company in rows:
        if (
            normalize_company(company) == norm.company_key
            and normalize_title(title) == norm.title_key
        ):
            return int(offer_id)
    return None


async def _fillable(session: AsyncSession, offer_id: int, draft: Draft) -> list[str]:
    offer = await session.get(Offer, offer_id)
    if offer is None:
        return []
    fields = [
        name
        for name in ("company", "location", "description")
        if not (getattr(offer, name) or "").strip() and (getattr(draft, name) or "").strip()
    ]
    if draft.url and await _manual_link(session, offer_id) is None:
        fields.append("url")
    return fields


async def _manual_link(session: AsyncSession, offer_id: int) -> OfferLink | None:
    return await session.scalar(
        select(OfferLink).where(OfferLink.offer_id == offer_id, OfferLink.source == SOURCE)
    )


async def fill(runtime: Runtime, offer_id: int, draft: Draft) -> list[str]:
    """Compléter l'offre déjà là avec l'annonce relue : seulement ses champs vides, rien n'est
    remplacé ni effacé. Le texte arrivé, la note faite sur l'extrait est refaite (docs/111)."""
    async with runtime.sessionmaker.begin() as session:
        # Relue sous la RLS du compte : l'id vient de la recherche du doublon, jamais du client.
        offer = await session.get(Offer, offer_id)
        if offer is None:
            return []
        filled: list[str] = []
        company = (draft.company or "").strip()[:300]
        if not (offer.company or "").strip() and company:
            offer.company = company
            filled.append("company")
        location = (draft.location or "").strip()[:300]
        if not (offer.location or "").strip() and location:
            offer.location = location
            offer.canton = offer.canton or canton_of(location)
            if offer.rate_min is None:
                offer.rate_min, offer.rate_max = parse_rate(location)
            filled.append("location")
        description = (draft.description or "").strip()
        if not (offer.description or "").strip() and description:
            offer.description = description
            offer.snippet = offer.snippet or description[:500]
            filled.append("description")
        if draft.url and await _manual_link(session, offer_id) is None:
            session.add(
                OfferLink(offer_id=offer_id, source=SOURCE, external_id=None, url=draft.url)
            )
            filled.append("url")
    log.info("manual_offer_filled", offer=offer_id, fields=filled)
    return filled


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
        existing = await same_offer(session, norm)
        if existing is not None:
            return existing
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


# --- Compléter une offre déjà reçue -----------------------------------------------------
# Une offre venue d'une alerte n'a parfois que l'extrait : sa note est provisoire. Sur sa fiche,
# on lit l'annonce par son lien (balisage JobPosting, puis texte principal), en respectant le
# robots.txt du site, ou on colle son texte. Rien ne contourne une connexion ou un captcha.

# Texte collé : en dessous, ce n'est pas une annonce complète.
MIN_PASTED = 200
# Les liens essayés, au plus (employeur, puis annonces d'origine).
MAX_LINKS = 3
ROBOTS_AGENT = "jobA1"


async def fetch_robots(url: str) -> str | None:
    """Le robots.txt du site de `url` ; None s'il n'y en a pas (réponse 4xx). Un site qui ne
    répond pas (5xx, réseau) est traité comme fermé : ReadProblem."""
    parts = urlsplit(url)
    robots = f"https://{parts.hostname}/robots.txt"
    async with httpx.AsyncClient(
        timeout=TIMEOUT_SECONDS, follow_redirects=False, headers={"User-Agent": logos.USER_AGENT}
    ) as client:
        try:
            data, _final = await logos._get(client, robots, MAX_PAGE_BYTES)
        except logos.Refused as exc:
            raise ReadProblem(f"Lien refusé : {exc}.") from exc
        except httpx.HTTPStatusError as exc:
            if 400 <= exc.response.status_code < 500:
                return None
            raise ReadProblem(
                "Le site ne répond pas : colle le texte de l'annonce.", paste=True
            ) from exc
        except httpx.HTTPError as exc:
            raise ReadProblem(
                "Le site ne répond pas : colle le texte de l'annonce.", paste=True
            ) from exc
    return data.decode("utf-8", errors="replace")


async def robots_allowed(url: str, cache: dict[str, str | None] | None = None) -> bool:
    """Le robots.txt du site permet-il à jobA1 de lire cette page ? (RFC 9309) `cache` :
    les robots.txt déjà lus pendant cette lecture, par hôte."""
    host = urlsplit(url).hostname or ""
    if cache is not None and host in cache:
        content = cache[host]
    else:
        content = await fetch_robots(url)
        if cache is not None:
            cache[host] = content
    if content is None:
        return True
    parser = RobotFileParser()
    parser.parse(content.splitlines())
    return parser.can_fetch(ROBOTS_AGENT, url)


def main_text(page: str) -> str:
    """Le texte principal de la page : `<main>` ou `<article>` s'il y en a, sinon le corps."""
    soup = BeautifulSoup(page, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "form", "aside"]):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    return " ".join(root.get_text(" ").split())


ROBOTS_REFUSED = "Ce site interdit la lecture par un robot : colle le texte de l'annonce."


async def read_link(url: str) -> str:
    """Le texte de l'annonce lu à `url` : la description du JobPosting, sinon le texte
    principal. Sans IA : l'offre a déjà son titre, son entreprise et son lieu. Le robots.txt
    est lu pour chaque hôte rencontré, redirections comprises, avant d'y charger une page."""
    robots: dict[str, str | None] = {}

    async def robots_first(hop: str) -> None:
        # Chaque adresse est vérifiée : une redirection peut mener à un autre hôte, ou à un
        # chemin que le robots.txt du même hôte interdit.
        if not await robots_allowed(hop, robots):
            raise ReadProblem(ROBOTS_REFUSED, paste=True)

    page = await fetch_page(url, robots_first)
    posting = job_posting(page)
    found = jobposting.text(posting.get("description")) if posting else None
    if not found or len(found) < MIN_PASTED:
        found = main_text(page)
    if len(found) < MIN_PASTED:
        raise ReadProblem(
            "Cette page ne montre pas d'annonce lisible (connexion demandée ?) : "
            "colle le texte de l'annonce.",
            paste=True,
        )
    return found[:MAX_TEXT]


def offer_urls(offer: Offer, links: list[str]) -> list[str]:
    """Les liens à lire, dans l'ordre : l'annonce chez l'employeur, puis celles des alertes."""
    seen: list[str] = []
    for url in [offer.employer_url, *links]:
        if url and url.startswith("https://") and not url.startswith(NO_LINK) and url not in seen:
            seen.append(url)
    return seen[:MAX_LINKS]


async def clean_pasted(session: AsyncSession, text: str) -> str:
    """Le texte collé nettoyé comme à l'ajout (espaces resserrés, nom de la personne retiré)."""
    identity = await load_identity(session)
    clean = " ".join(text.split())
    for name in (identity.name or "").split():
        if len(name) > 2:
            clean = re.sub(re.escape(name), "[nom retiré]", clean, flags=re.IGNORECASE)
    return clean[:MAX_TEXT]


class OfferNotFound(Exception):
    """Offre absente pour ce compte (RLS) : 404."""


class NoAnnouncement(Exception):
    """Candidature spontanée : il n'y a pas d'annonce à compléter."""


async def _load(session: AsyncSession, offer_id: int) -> tuple[Offer, list[str]]:
    # L'id vient du client : relu sous la RLS du compte en cours (C-5).
    offer = await session.get(Offer, offer_id)
    if offer is None:
        raise OfferNotFound
    if offer.spontaneous:
        raise NoAnnouncement
    links = list(
        await session.scalars(
            select(OfferLink.url).where(OfferLink.offer_id == offer_id).order_by(OfferLink.id)
        )
    )
    return offer, links


async def save_description(runtime: Runtime, offer_id: int, text: str, source: str) -> int | None:
    """Le texte complet enregistré : la note n'est plus partielle. L'offre repasse par le filtre
    (le texte peut révéler un contrat ou une langue), puis elle est renotée tout de suite.
    Rend la nouvelle note (None : pas d'IA ou plafond, elle suivra au prochain passage)."""
    async with runtime.sessionmaker.begin() as session:
        offer, _links = await _load(session, offer_id)
        offer.description = text
        if not offer.snippet:
            offer.snippet = text[:500]
    await run_filter(runtime)
    log.info("offer_description_completed", offer=offer_id, source=source)
    if not runtime.settings.llm_configured:
        return None
    return await scoring_service.score_offer(runtime, offer_id)


async def check_offer(runtime: Runtime, offer_id: int) -> None:
    """L'offre existe pour ce compte et a une annonce ; sinon OfferNotFound ou NoAnnouncement."""
    async with runtime.sessionmaker() as session:
        await _load(session, offer_id)


async def read_offer(runtime: Runtime, offer_id: int) -> int | None:
    """« Lire l'annonce maintenant » : le premier lien lisible ; sinon ReadProblem."""
    async with runtime.sessionmaker() as session:
        offer, links = await _load(session, offer_id)
        urls = offer_urls(offer, links)
    if not urls:
        raise ReadProblem("Cette offre n'a pas de lien : colle le texte de l'annonce.", paste=True)
    problem: ReadProblem | None = None
    for url in urls:
        try:
            found = await read_link(url)
        except ReadProblem as exc:
            problem = exc
            continue
        return await save_description(runtime, offer_id, found, "page")
    assert problem is not None
    raise problem
