"""Voir l'offre chez l'employeur (docs/20 §2), du moins cher au plus cher :

1. page carrières du site de l'entreprise, quand il est connu ;
2. liste publique des postes de l'outil de recrutement reconnu sur ce site (Greenhouse,
   Lever, SmartRecruiters, Personio : adresses vérifiées le 2026-10-07), sans IA ;
3. recherche sur Internet par l'IA (Claude Haiku), qui ne reçoit que l'entreprise, le poste
   et la ville.

Une page trouvée par le site ou par l'IA n'est retenue que si elle contient le titre du poste
et le nom de l'entreprise. Les requêtes passent par les garde-fous des logos.
"""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import resources
from typing import Any
from urllib.parse import quote, urljoin, urlsplit

import anthropic
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.normalize import normalize_text
from jobbot.db.models import Company, Offer
from jobbot.llm.client import Refused
from jobbot.log import get_logger
from jobbot.logos import service as logos
from jobbot.registry.service import name_key
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, budget_state, record_call

log = get_logger(__name__)

USER_AGENT = "job-bot/0.13 (usage personnel)"
MAX_PAGE_BYTES = 2_000_000
MAX_LIST_BYTES = 5_000_000
TITLE_MATCH = 0.75
RECHECK_AFTER = timedelta(days=3)
ESTIMATE_USD = Decimal("0.04")
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 3_000
MAX_SEARCHES = 3
INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath("prompts/employer-offer-v1.md").read_text("utf-8")
)
_ANSWER = re.compile(r"<reponse>\s*(\{.*?\})\s*</reponse>", re.S)

# Plateformes d'annonces : jamais retenues comme « chez l'employeur ».
PROXY_HOSTS = (
    "jobup.ch",
    "jobs.ch",
    "indeed.",
    "linkedin.com",
    "glassdoor.",
    "jobscout24.",
    "job-room.ch",
    "monster.",
    "stepstone.",
    "google.",
)
# Annuaires : un lien vers eux ne dit rien du site de l'entreprise.
DIRECTORY_HOSTS = ("local.ch", "search.ch", "moneyhouse.ch", "zefix.ch", "uid.admin.ch")
# Agences de placement connues et formules d'annonce pour un client (docs/20 §2.4).
AGENCIES = (
    "adecco",
    "manpower",
    "randstad",
    "kelly services",
    "michael page",
    "page personnel",
    "hays",
    "robert half",
    "spring professional",
    "gi group",
    "careerplus",
    "coople",
    "interiman",
    "synergie",
    "proman",
    "people one",
    "pro personal",
    "universal job",
    "lhh",
    "kforce",
)
CLIENT_PHRASES = (
    "pour notre client",
    "pour le compte de notre client",
    "fur unseren kunden",
    "im auftrag unseres kunden",
    "on behalf of our client",
    "for our client",
)
_CAREERS = re.compile(
    r"emploi|carri|career|jobs?\b|stellen|karriere|rejoindre|join-us|recrut", re.I
)
_GENDER = re.compile(
    r"\((?:[hfmwdx]\s*/\s*)+[hfmwdx]\)|\b(?:[hfmwdx]/)+[hfmwdx]\b|\d{2,3}\s*%", re.I
)
ATS_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "greenhouse",
        re.compile(
            r"(?:boards|job-boards)\.greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_-]+)", re.I
        ),
    ),
    ("lever", re.compile(r"jobs\.lever\.co/([a-z0-9_.-]+)", re.I)),
    (
        "smartrecruiters",
        re.compile(r"(?:jobs|careers)\.smartrecruiters\.com/([A-Za-z0-9_-]+)", re.I),
    ),
    ("personio", re.compile(r"([a-z0-9-]+)\.jobs\.personio\.(?:de|com|ch)", re.I)),
]


@dataclass(frozen=True)
class Found:
    url: str | None
    source: str | None  # site | ats | web
    status: str  # found | not_found | agency


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=20, follow_redirects=False, headers={"User-Agent": USER_AGENT})


def _host(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def is_proxy(url: str) -> bool:
    host = _host(url)
    return any(p in host for p in PROXY_HOSTS)


def _words(text: str) -> list[str]:
    return [w for w in normalize_text(_GENDER.sub(" ", text)).split() if len(w) > 1]


def title_matches(wanted: str, candidate: str) -> bool:
    """Les mots du titre recherché (sans « (h/f) » ni taux) se retrouvent dans le candidat."""
    words = _words(wanted)
    if not words:
        return False
    have = set(_words(candidate))
    return sum(w in have for w in words) / len(words) >= TITLE_MATCH


def is_agency(company: str | None, text: str | None) -> bool:
    name = f" {normalize_text(company or '')} "
    if any(f" {normalize_text(a)} " in name for a in AGENCIES):
        return True
    body = normalize_text(text or "")
    return any(normalize_text(p) in body for p in CLIENT_PHRASES)


def detect_ats(html: str) -> str | None:
    for name, pattern in ATS_PATTERNS:
        if match := pattern.search(html):
            return f"{name}:{match.group(1)}"
    return None


def _site_domain(url: str) -> str:
    """« jobs.exemple.ch » → « exemple.ch » (pour reconnaître les sous-domaines du site)."""
    return ".".join(_host(url).split(".")[-2:])


def careers_link(html: str, base: str) -> str | None:
    """Lien « Emplois », « Carrières »… d'une page : sur le même site (sous-domaines compris)
    ou vers un outil de recrutement reconnu."""
    soup = BeautifulSoup(html, "html.parser")
    domain = _site_domain(base)
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"])
        label = anchor.get_text(" ", strip=True)
        if not (_CAREERS.search(label) or _CAREERS.search(href)):
            continue
        url = urljoin(base, href)
        if not url.startswith("https://") or is_proxy(url) or url.rstrip("/") == base.rstrip("/"):
            continue
        if _site_domain(url) == domain or detect_ats(url):
            return url
    return None


def anchor_for_title(html: str, base: str, title: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        if title_matches(title, anchor.get_text(" ", strip=True)):
            url = urljoin(base, str(anchor["href"]))
            if url.startswith("https://") and not is_proxy(url):
                return url
    return None


async def _get_text(
    client: httpx.AsyncClient, url: str, limit: int = MAX_PAGE_BYTES
) -> tuple[str, str]:
    data, final = await logos._get(client, url, limit)
    return data.decode("utf-8", errors="replace"), final


async def ats_postings(client: httpx.AsyncClient, ats: str, title: str) -> list[tuple[str, str]]:
    """(titre, adresse) des postes ouverts, depuis la liste publique de l'outil."""
    kind, _, key = ats.partition(":")
    slug = quote(key, safe="")
    if kind == "greenhouse":
        text, _ = await _get_text(
            client, f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", MAX_LIST_BYTES
        )
        return [(j["title"], j["absolute_url"]) for j in json.loads(text).get("jobs", [])]
    if kind == "lever":
        text, _ = await _get_text(
            client, f"https://api.lever.co/v0/postings/{slug}?mode=json", MAX_LIST_BYTES
        )
        return [(p["text"], p["hostedUrl"]) for p in json.loads(text)]
    if kind == "smartrecruiters":
        url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=50&q={quote(title)}"
        text, _ = await _get_text(client, url, MAX_LIST_BYTES)
        return [
            (p["name"], f"https://jobs.smartrecruiters.com/{slug}/{p['id']}")
            for p in json.loads(text).get("content", [])
        ]
    if kind == "personio":
        text, _ = await _get_text(client, f"https://{slug}.jobs.personio.de/xml", MAX_LIST_BYTES)
        soup = BeautifulSoup(text, "html.parser")
        found: list[tuple[str, str]] = []
        for position in soup.find_all("position"):
            name, ident = position.find("name"), position.find("id")
            if name is not None and ident is not None:
                job_id = ident.get_text(strip=True)
                found.append(
                    (name.get_text(strip=True), f"https://{slug}.jobs.personio.de/job/{job_id}")
                )
        return found
    return []


async def verify(client: httpx.AsyncClient, url: str, title: str, company: str | None) -> bool:
    """La page contient le titre du poste et le nom de l'entreprise, et n'est pas une
    plateforme d'annonces."""
    if not url.startswith("https://") or is_proxy(url):
        return False
    try:
        html, final = await _get_text(client, url)
    except (logos.Refused, httpx.HTTPError):
        return False
    if is_proxy(final):
        return False
    text = BeautifulSoup(html, "html.parser").get_text(" ")
    if not title_matches(title, text):
        return False
    company_words = [w for w in _words(company or "") if len(w) > 2][:2]
    page = set(_words(text))
    return all(w in page for w in company_words)


def _website(offer: Offer, company: Company | None) -> str | None:
    for url in (offer.company_website, company.source_url if company else None):
        if (
            url
            and url.startswith("https://")
            and not is_proxy(url)
            and not any(d in _host(url) for d in DIRECTORY_HOSTS)
        ):
            parts = urlsplit(url)
            return f"{parts.scheme}://{parts.netloc}/"
    return None


async def _from_site(
    session: AsyncSession, client: httpx.AsyncClient, offer: Offer, company: Company | None
) -> Found | None:
    ats: str | None
    careers: str | None
    if company and company.ats:
        ats = company.ats
        careers = company.careers_url
    else:
        website = _website(offer, company)
        if website is None:
            return None
        try:
            home, home_url = await _get_text(client, website)
        except (logos.Refused, httpx.HTTPError):
            return None
        ats = detect_ats(home)
        careers = careers_link(home, home_url)
        if careers and not ats:
            try:
                careers_html, careers_final = await _get_text(client, careers)
                ats = detect_ats(careers_html)
                # Page carrières qui renvoie vers la liste des postes (sous-domaine « jobs. »,
                # outil de recrutement) : un pas de plus, pas davantage.
                deeper = None if ats else careers_link(careers_html, careers_final)
                if deeper and deeper != careers:
                    careers_html, careers_final = await _get_text(client, deeper)
                    ats = detect_ats(careers_html)
                    careers = deeper
                url = None if ats else anchor_for_title(careers_html, careers_final, offer.title)
                if url and await verify(client, url, offer.title, offer.company):
                    await _remember(session, offer, careers, ats)
                    return Found(url, "site", "found")
            except (logos.Refused, httpx.HTTPError):
                careers = None
        await _remember(session, offer, careers, ats)
    if ats:
        try:
            postings = await ats_postings(client, ats, offer.title)
        except (logos.Refused, httpx.HTTPError, ValueError, KeyError, TypeError):
            postings = []
        for title, url in postings:
            if title_matches(offer.title, title) and url.startswith("https://"):
                return Found(url, "ats", "found")
    return None


async def _remember(
    session: AsyncSession, offer: Offer, careers: str | None, ats: str | None
) -> None:
    if not offer.company:
        return
    values = {"careers_url": careers, "ats": ats, "careers_checked_at": datetime.now(UTC)}
    await session.execute(
        insert(Company)
        .values(
            name_key=name_key(offer.company),
            looked_up_at=datetime.now(UTC),
            candidates=[],
            **values,
        )
        .on_conflict_do_update(index_elements=["name_key"], set_=values)
    )


def request_params(company: str, title: str, town: str | None) -> dict[str, Any]:
    def clean(value: str) -> str:
        return " ".join(value.replace("<", " ").replace(">", " ").split())[:150]

    content = (
        f"<entreprise>{clean(company)}</entreprise>\n<poste>{clean(title)}</poste>\n"
        f"<ville>{clean(town or 'inconnue')}</ville>"
    )
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": content}],
        "tools": [
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": MAX_SEARCHES,
                "user_location": {"type": "approximate", "country": "CH"},
            }
        ],
    }


def parse_answer(text: str) -> str | None:
    matches = _ANSWER.findall(text)
    if not matches:
        return None
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return None
    url = data.get("url") if isinstance(data, dict) and data.get("found") is True else None
    return (
        url.strip()[:1000] if isinstance(url, str) and url.strip().startswith("https://") else None
    )


class EmployerUnavailable(Exception):
    """IA nécessaire mais non configurée, plafond atteint ou compte indisponible."""


async def _from_web(runtime: Runtime, client: httpx.AsyncClient, offer: Offer) -> Found | None:
    settings = runtime.settings
    if not settings.llm_configured or not offer.company:
        return None
    async with runtime.sessionmaker() as session:
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if spend + ESTIMATE_USD * rate > budget:
        raise EmployerUnavailable("plafond mensuel de l'IA atteint")
    try:
        raw = await scoring_service.make_client(settings).score(
            request_params(offer.company, offer.title, offer.location)
        )
    except Refused:
        return None
    except anthropic.APIStatusError as exc:
        if problem := account_problem(exc):
            raise EmployerUnavailable(problem) from None
        raise
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=offer.id, rate=rate, purpose="employer")
    url = parse_answer(raw.text)
    if url and await verify(client, url, offer.title, offer.company):
        return Found(url, "web", "found")
    return None


def eligible(offer: Offer) -> bool:
    """Lien vers l'employeur déjà connu (annonce jobup) : rien à chercher."""
    return not (
        offer.apply_kind == "external" and offer.apply_url and not is_proxy(offer.apply_url)
    )


async def find(runtime: Runtime, offer_id: int, *, use_web: bool = True) -> Found | None:
    """Cherche l'annonce chez l'employeur et l'enregistre sur l'offre."""
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            return None
        company = await session.get(Company, name_key(offer.company)) if offer.company else None
    if not eligible(offer):
        return None
    result: Found | None
    if is_agency(offer.company, offer.description or offer.snippet):
        result = Found(None, None, "agency")
    else:
        async with _client() as client:
            async with runtime.sessionmaker.begin() as session:
                result = await _from_site(session, client, offer, company)
            if result is None and use_web:
                result = await _from_web(runtime, client, offer)
        result = result or Found(None, None, "not_found")
    async with runtime.sessionmaker.begin() as session:
        stored = await session.get(Offer, offer_id)
        if stored is not None:
            stored.employer_url = result.url
            stored.employer_url_source = result.source
            stored.employer_status = result.status
            stored.employer_checked_at = datetime.now(UTC)
    log.info("employer_search", offer_id=offer_id, status=result.status, source=result.source)
    return result


async def recheck(runtime: Runtime, offer: Offer) -> None:
    """Annonce disparue chez l'employeur : le lien est retiré."""
    alive = False
    if offer.employer_url:
        async with _client() as client:
            try:
                await logos._get(client, offer.employer_url, MAX_PAGE_BYTES)
                alive = True
            except (logos.Refused, httpx.HTTPError):
                alive = False
    async with runtime.sessionmaker.begin() as session:
        stored = await session.get(Offer, offer.id)
        if stored is not None:
            if not alive:
                stored.employer_url = None
                stored.employer_url_source = None
                stored.employer_status = "gone"
            stored.employer_checked_at = datetime.now(UTC)


async def candidates(session: AsyncSession, threshold: int, limit: int) -> list[int]:
    from jobbot.db.models import Evaluation, OfferStatus

    rows = await session.scalars(
        select(Offer.id)
        .join(Evaluation, Evaluation.offer_id == Offer.id)
        .where(
            Evaluation.score >= threshold,
            Offer.employer_checked_at.is_(None),
            Offer.expired_at.is_(None),
            Offer.status.in_(
                [OfferStatus.NEW, OfferStatus.TO_REVIEW, OfferStatus.LATER, OfferStatus.PREPARING]
            ),
        )
        .order_by(Evaluation.score.desc())
        .limit(limit)
    )
    return list(rows)


async def stale(session: AsyncSession, limit: int) -> list[Offer]:
    limit_date = datetime.now(UTC) - RECHECK_AFTER
    rows = await session.scalars(
        select(Offer)
        .where(
            Offer.employer_url.is_not(None),
            Offer.employer_checked_at < limit_date,
            Offer.expired_at.is_(None),
        )
        .limit(limit)
    )
    return list(rows)
