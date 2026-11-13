"""Inventaire des pages carrières d'employeurs vaudois (docs/145, étape 1).

Le script ne touche ni à l'app ni à la base : il lit des pages publiques et écrit un tableau.

    python3 scripts/inventaire_employeurs.py

Il lit les employeurs de docs/inventaire-employeurs/employeurs-vaud.csv et écrit
docs/inventaire-employeurs/inventaire.md (tableau et seuil) et inventaire.csv.

Pour chaque employeur : robots.txt, la page carrières (en suivant au plus 3 liens depuis
l'adresse de départ), le logiciel de recrutement reconnu, jusqu'à 30 pages d'offres lues
(ou le flux public du logiciel), le balisage `JobPosting`, le nombre d'offres en Vaud ce jour,
la page des conditions d'utilisation, puis le verdict « lisible » ou « non lisible » selon la
définition fixée le 13.11.2026 (docs/145 §2).

Règles suivies : robots.txt lu avant toute page (refus = la page n'est pas lue), `Crawl-delay`
respecté (2 s au moins entre deux pages d'un même site), un robot qui se nomme avec un contact,
une seule lecture par page. Rien de personnel n'est gardé : seulement des noms d'employeurs,
des titres d'offres, des lieux et des dates.

La colonne « conditions » est une proposition : chaque « interdite » ou « permise » se relit
à la main, et « pas de page trouvée » compte comme non lisible tant qu'on ne l'a pas vérifiée.

Seulement la bibliothèque standard de Python (3.11 ou plus).
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "docs" / "inventaire-employeurs"
USER_AGENT = "jobA1-inventaire/1.1 (+https://joba1.ch)"
MIN_DELAY = 2.0
TIMEOUT = 20
MAX_BYTES = 3_000_000
MAX_HOPS = 3
MAX_OFFERS = 30
THRESHOLD = 0.5


# --- Lecture des pages -------------------------------------------------------------------


@dataclass
class Page:
    status: int
    url: str
    text: str


Fetcher = Callable[[str], Page]


def http_fetch(url: str) -> Page:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "fr-CH,fr;q=0.9"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read(MAX_BYTES)
            charset = response.headers.get_content_charset() or "utf-8"
            return Page(response.status, response.geturl(), raw.decode(charset, errors="replace"))
    except urllib.error.HTTPError as error:
        return Page(error.code, url, "")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return Page(0, url, "")


class Polite:
    """Lit les pages en respectant robots.txt et un délai par site."""

    def __init__(self, fetch: Fetcher = http_fetch, sleep: Callable[[float], None] = time.sleep) -> None:
        self.fetch = fetch
        self.sleep = sleep
        self.robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.robots_state: dict[str, str] = {}
        self.sitemaps: dict[str, list[str]] = {}
        self.last: dict[str, float] = {}
        self.lock = threading.Lock()

    @staticmethod
    def host(url: str) -> str:
        parts = urllib.parse.urlsplit(url)
        return f"{parts.scheme}://{parts.netloc}"

    def rules(self, url: str) -> urllib.robotparser.RobotFileParser | None:
        """Les règles du site ; None = site injoignable (on ne lit rien)."""
        host = self.host(url)
        if host not in self.robots:
            page = self._get(host + "/robots.txt")
            parser = urllib.robotparser.RobotFileParser()
            if page.status == 0 or page.status >= 500:
                self.robots[host], self.robots_state[host] = None, "injoignable"
                return None
            if page.status in (401, 403):
                parser.disallow_all = True
                self.robots_state[host] = "interdit"
            elif page.status >= 400:
                parser.allow_all = True
                self.robots_state[host] = "absent"
            else:
                parser.parse(page.text.splitlines())
                self.sitemaps[host] = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", page.text)
                self.robots_state[host] = "présent"
            self.robots[host] = parser
        return self.robots[host]

    def allowed(self, url: str) -> bool:
        rules = self.rules(url)
        return rules is not None and rules.can_fetch(USER_AGENT, url)

    def delay(self, url: str) -> float:
        rules = self.robots.get(self.host(url))
        asked = rules.crawl_delay(USER_AGENT) if rules else None
        return max(MIN_DELAY, float(asked or 0))

    def _get(self, url: str) -> Page:
        host = self.host(url)
        with self.lock:
            wait = self.last.get(host, 0) + self.delay(url) - time.monotonic()
        if wait > 0:
            self.sleep(wait)
        page = self.fetch(url)
        with self.lock:
            self.last[host] = time.monotonic()
        return page

    def get(self, url: str) -> Page | None:
        """La page, ou None si robots.txt l'interdit ou si le site est injoignable."""
        if not self.allowed(url):
            return None
        page = self._get(url)
        # Une redirection vers un autre site : ses propres règles s'appliquent aussi.
        if self.host(page.url) != self.host(url) and not self.allowed(page.url):
            return None
        return page


# --- Ce qu'on reconnaît dans une page ----------------------------------------------------

# (nom, cas, motif). Cas 1 = flux public fait pour être lu ; cas 3 = logiciel courant en Suisse
# sans flux public ; « autre » = connu, sans cas fixé.
PLATFORMS: list[tuple[str, str, re.Pattern[str]]] = [
    ("Personio", "1", re.compile(r"[\w-]+\.jobs\.personio\.(?:de|com)", re.I)),
    ("Greenhouse", "1", re.compile(r"(?:job-)?boards(?:-api)?\.greenhouse\.io", re.I)),
    ("Lever", "1", re.compile(r"jobs\.lever\.co|api\.lever\.co", re.I)),
    ("Recruitee", "1", re.compile(r"[\w-]+\.recruitee\.com", re.I)),
    ("Workable", "1", re.compile(r"apply\.workable\.com", re.I)),
    ("SmartRecruiters", "1", re.compile(r"(?:jobs|careers|api)\.smartrecruiters\.com", re.I)),
    ("Ashby", "1", re.compile(r"jobs\.ashbyhq\.com|api\.ashbyhq\.com", re.I)),
    ("SuccessFactors", "3", re.compile(r"successfactors|sapsf\.|jobs\.sap\.com|career\d*\.sap|rmkcdn|/go/[\w-]+/\d{5,}/", re.I)),
    ("Refline", "3", re.compile(r"refline\.ch", re.I)),
    ("Abacus / umantis", "3", re.compile(r"umantis\.com|abacuscity|abacus\.ch/.*recruit", re.I)),
    ("Prospective", "3", re.compile(r"prospective\.ch|jobs\.prospective", re.I)),
    ("Workday", "autre", re.compile(r"myworkdayjobs\.com|wd\d+\.myworkday", re.I)),
    ("Beehire", "autre", re.compile(r"beehire\.com", re.I)),
    ("Teamtailor", "autre", re.compile(r"teamtailor\.com", re.I)),
    ("Softgarden", "autre", re.compile(r"softgarden\.io", re.I)),
    ("Taleo", "autre", re.compile(r"taleo\.net", re.I)),
]

LD_JSON = re.compile(r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", re.S | re.I)
LINK = re.compile(r"<a\b[^>]*href=[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", re.S | re.I)
FRAME = re.compile(r"<iframe\b[^>]*src=[\"']([^\"']+)[\"']", re.I)
ASSET = re.compile(r"\.(?:pdf|jpe?g|png|gif|svg|webp|docx?|xlsx?|zip|mp4|ics)(?:$|\?)", re.I)
CAREER = re.compile(r"carri[eè]res?|emplois?\b|karriere|careers?\b|jobs?\b|recrutement|nous rejoindre|rejoignez", re.I)
OFFERS = re.compile(
    r"offres?\s+d.emploi|postes?\s+(?:vacants?|ouverts?|à pourvoir|disponibles?)|toutes les offres|voir les offres|"
    r"stellenangebote|offene stellen|job openings|open positions|vacanc|current openings|search jobs|"
    r"offres-d-emploi|postes-vacants|job-openings|stellenangebote|/jobs/?$|/emplois/?$|/offres/?$",
    re.I,
)
OFFER_WORD = re.compile(
    r"/(?:job|jobs|emploi|emplois|offre|offres|offres-d-emploi|poste|postes|stelle|stellen|stellenangebote|"
    r"vacancy|vacancies|position|positions|career|careers|karriere|annonce|detail|requisition)s?/",
    re.I,
)
# Une page d'offre porte un numéro (3 chiffres au moins) ou un identifiant : ça écarte les
# pages « pourquoi nous rejoindre » rangées sous /carrieres/.
OFFER_ID = re.compile(r"\d{3,}|[0-9a-f]{8}-[0-9a-f]{4}-", re.I)


def is_offer(url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    target = parts.path + ("?" + parts.query if parts.query else "")
    return bool(OFFER_WORD.search(parts.path + "/")) and bool(OFFER_ID.search(target))


TERMS = re.compile(
    r"conditions[-_ ]g[eé]n[eé]rales|conditions[-_ ]d.utilisation|\bcgu\b|mentions?[-_ ]l[eé]gales|"
    r"nutzungsbedingungen|terms|rechtliche|disclaimer|informations?[-_ ]juridiques|legal|impressum",
    re.I,
)
ROBOT_WORDS = re.compile(
    r"robot|automati|scrap|crawl|aspir|extraction|extraire|data[- ]mining|moissonn|spider|bots?\b",
    re.I,
)
FORBID = re.compile(
    r"interdi|prohib|not permitted|untersagt|nicht gestattet|pas autoris|n.est pas permis|"
    r"sans (?:l.)?(?:accord|autorisation|consentement)|without (?:the )?(?:prior )?(?:written )?(?:consent|permission)",
    re.I,
)
ALLOW = re.compile(r"autoris[ée]e?s?\b|permis\b|permitted|gestattet|erlaubt", re.I)


def plain(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def platform(*texts: str) -> tuple[str, str]:
    for name, case, pattern in PLATFORMS:
        if any(pattern.search(text) for text in texts):
            return name, case
    return "", ""


def postings(page: str) -> list[dict[str, object]]:
    """Les `JobPosting` (schema.org) des blocs JSON-LD de la page."""
    found: list[dict[str, object]] = []
    for match in LD_JSON.finditer(page):
        try:
            data = json.loads(html.unescape(match.group(1)).strip())
        except json.JSONDecodeError:
            continue
        stack: list[object] = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                kind = item.get("@type")
                kinds = kind if isinstance(kind, list) else [kind]
                if "JobPosting" in kinds:
                    found.append(item)
                else:
                    stack.extend(v for v in item.values() if isinstance(v, (list, dict)))
    return found


def posting_place(posting: dict[str, object]) -> tuple[str, str]:
    """(lieu, pays) d'un `JobPosting`, tous lieux mis bout à bout."""
    places = posting.get("jobLocation")
    places = places if isinstance(places, list) else [places]
    parts, countries = [], []
    for place in places:
        address = place.get("address") if isinstance(place, dict) else None
        if isinstance(address, dict):
            parts += [str(address.get(k) or "") for k in ("addressLocality", "addressRegion", "postalCode")]
            country = address.get("addressCountry")
            countries.append(str(country.get("name") if isinstance(country, dict) else country or ""))
        elif isinstance(address, str):
            parts.append(address)
    country = next((c for c in countries if c), "")
    return " ".join(p for p in parts if p), country


def complete(posting: dict[str, object]) -> bool:
    """Un `JobPosting` utilisable : titre, lieu et date de publication."""
    place, _ = posting_place(posting)
    remote = str(posting.get("jobLocationType", "")).upper() == "TELECOMMUTE"
    return bool(posting.get("title")) and bool(posting.get("datePosted")) and bool(place or remote)


def links(page: Page) -> list[tuple[str, str]]:
    found = []
    for href, label in LINK.findall(page.text):
        url = urllib.parse.urljoin(page.url, html.unescape(href.strip()))
        if url.startswith("http") and not ASSET.search(url):
            found.append((url, plain(label)))
    for src in FRAME.findall(page.text):
        url = urllib.parse.urljoin(page.url, html.unescape(src.strip()))
        if url.startswith("http"):
            found.append((url, "cadre intégré"))
    return found


def next_pages(page: Page) -> list[str]:
    """Les liens à suivre vers la liste des offres, du plus au moins probable."""
    scored: list[tuple[int, str]] = []
    here = urllib.parse.urlsplit(page.url).netloc
    for url, label in links(page):
        path = urllib.parse.urlsplit(url).path
        if url.rstrip("/") == page.url.rstrip("/"):
            continue
        if platform(url)[0]:
            score = 3
        elif OFFERS.search(label) or OFFERS.search(path):
            score = 2
        elif CAREER.search(label) or CAREER.search(path):
            score = 1
        else:
            continue
        if urllib.parse.urlsplit(url).netloc != here and score < 3:
            # Un autre site n'est suivi que s'il s'agit d'un logiciel de recrutement connu ou
            # d'un sous-domaine d'emploi de l'employeur (jobs.…, careers.…, emploi.…).
            if not re.match(r"(?:jobs?|careers?|karriere|emplois?|career|stellen)\.", urllib.parse.urlsplit(url).netloc):
                continue
        scored.append((score, url))
    seen: set[str] = set()
    ordered = []
    for _score, url in sorted(scored, key=lambda s: -s[0]):
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


def offer_links(page: Page) -> list[str]:
    found = []
    for url, _label in links(page):
        if is_offer(url) and url not in found:
            found.append(url)
    return found


def terms_link(page: Page) -> str | None:
    for url, label in links(page):
        if TERMS.search(label) or TERMS.search(urllib.parse.urlsplit(url).path):
            return url
    return None


def terms_verdict(text: str) -> tuple[str, str]:
    """« interdite », « permise » ou « rien », avec la phrase trouvée (à relire à la main)."""
    sentences = re.split(r"(?<=[.;!?])\s+", plain(text))
    allowed = ""
    for sentence in sentences:
        if not ROBOT_WORDS.search(sentence):
            continue
        if FORBID.search(sentence):
            return "interdite", sentence[:300]
        if ALLOW.search(sentence) and not allowed:
            allowed = sentence[:300]
    return ("permise", allowed) if allowed else ("rien", "")


# --- Flux publics du cas 1 ---------------------------------------------------------------


def _json(text: str) -> object:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def parse_personio(text: str) -> list[tuple[str, str, str]]:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        return []
    found = []
    for position in root.iter("position"):
        offices = [position.findtext("office") or ""] + [o.text or "" for o in position.iter("additionalOffice")]
        found.append((position.findtext("name") or "", " / ".join(o for o in offices if o), ""))
    return found


def parse_greenhouse(text: str) -> list[tuple[str, str, str]]:
    data = _json(text)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    return [(j.get("title", ""), (j.get("location") or {}).get("name", ""), "") for j in jobs if isinstance(j, dict)]


def parse_lever(text: str) -> list[tuple[str, str, str]]:
    data = _json(text)
    found = []
    for job in data if isinstance(data, list) else []:
        cats = job.get("categories") or {}
        places = " / ".join([cats.get("location") or "", *(cats.get("allLocations") or [])])
        found.append((job.get("text", ""), places, job.get("country") or ""))
    return found


def parse_recruitee(text: str) -> list[tuple[str, str, str]]:
    data = _json(text)
    offers = data.get("offers", []) if isinstance(data, dict) else []
    return [(o.get("title", ""), f"{o.get('city') or ''} {o.get('location') or ''}", o.get("country_code") or "") for o in offers]


def parse_workable(text: str) -> list[tuple[str, str, str]]:
    data = _json(text)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    return [(j.get("title", ""), f"{j.get('city') or ''} {j.get('state') or ''}", j.get("country") or "") for j in jobs]


def parse_smartrecruiters(text: str) -> list[tuple[str, str, str]]:
    data = _json(text)
    jobs = data.get("content", []) if isinstance(data, dict) else []
    found = []
    for job in jobs:
        place = job.get("location") or {}
        found.append((job.get("name", ""), f"{place.get('city') or ''} {place.get('region') or ''}", place.get("country") or ""))
    return found


def parse_ashby(text: str) -> list[tuple[str, str, str]]:
    data = _json(text)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    found = []
    for job in jobs:
        address = ((job.get("address") or {}).get("postalAddress")) or {}
        place = f"{job.get('location') or ''} {address.get('addressLocality') or ''} {address.get('addressRegion') or ''}"
        found.append((job.get("title", ""), place, address.get("addressCountry") or ""))
    return found


# (plateforme, motif qui donne le compte dans une adresse, adresse du flux, lecture)
FEEDS: dict[str, tuple[re.Pattern[str], Callable[[str], str], Callable[[str], list[tuple[str, str, str]]]]] = {
    "Personio": (re.compile(r"//([\w-]+)\.jobs\.personio\.(?:de|com)", re.I),
                 lambda s: f"https://{s}.jobs.personio.de/xml?language=fr", parse_personio),
    "Greenhouse": (re.compile(r"(?:job-)?boards\.greenhouse\.io/(?:embed/job_board\?for=)?([\w-]+)", re.I),
                   lambda s: f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs", parse_greenhouse),
    "Lever": (re.compile(r"jobs\.lever\.co/([\w.-]+)", re.I),
              lambda s: f"https://api.lever.co/v0/postings/{s}?mode=json", parse_lever),
    "Recruitee": (re.compile(r"//([\w-]+)\.recruitee\.com", re.I),
                  lambda s: f"https://{s}.recruitee.com/api/offers/", parse_recruitee),
    "Workable": (re.compile(r"apply\.workable\.com/([\w-]+)", re.I),
                 lambda s: f"https://apply.workable.com/api/v1/widget/accounts/{s}", parse_workable),
    "SmartRecruiters": (re.compile(r"(?:jobs|careers)\.smartrecruiters\.com/([\w-]+)", re.I),
                        lambda s: f"https://api.smartrecruiters.com/v1/companies/{s}/postings", parse_smartrecruiters),
    "Ashby": (re.compile(r"jobs\.ashbyhq\.com/([\w.-]+)", re.I),
              lambda s: f"https://api.ashbyhq.com/posting-api/job-board/{s}", parse_ashby),
}


def feed_account(name: str, *texts: str) -> str | None:
    pattern = FEEDS[name][0]
    for text in texts:
        if match := pattern.search(text):
            if match.group(1).lower() not in {"embed", "api", "www", "app", "j"}:
                return match.group(1)
    return None


# --- Lieux vaudois -----------------------------------------------------------------------

VAUD_TOWNS = """
lausanne renens prilly pully lutry epalinges ecublens crissier bussigny chavannes-pres-renens saint-sulpice
le mont-sur-lausanne romanel-sur-lausanne cheseaux-sur-lausanne belmont-sur-lausanne paudex savigny
morges preverenges tolochenaz saint-prex etoy allaman aubonne rolle gland nyon prangins eysins coppet founex
commugny mies tannay crans-pres-celigny cossonay penthalaz echallens yverdon-les-bains yverdon grandson orbe
vallorbe sainte-croix le sentier le chenit le brassus vevey corseaux corsier-sur-vevey la tour-de-peilz
blonay saint-legier montreux clarens villeneuve chexbres puidoux oron moudon lucens payerne avenches aigle
bex ollon villars-sur-ollon leysin chateau-d'oex villars-sainte-croix mex vufflens-la-ville apples biere
cheseaux mont-sur-lausanne dorigny chamblon montagny-pres-yverdon estavayer-le-lac
""".split()
VAUD_EXTRA = ["vaud", "waadt", "canton de vaud", "canton of vaud"]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[’`]", "'", text)


_VAUD = re.compile(
    r"(?<![\w-])(?:" + "|".join(re.escape(t) for t in sorted(VAUD_TOWNS + VAUD_EXTRA, key=len, reverse=True)) + r")(?![\w-])"
    r"|\(vd\)|,\s*vd\b|\bvd,|\bvd\s*$|\bch-vd\b|^vd$"
)


def in_vaud(place: str, country: str = "") -> bool:
    if country and normalize(country) not in {"ch", "che", "switzerland", "suisse", "schweiz", "svizzera"}:
        return False
    return bool(_VAUD.search(normalize(place)))


# --- L'inventaire ------------------------------------------------------------------------


@dataclass
class Employer:
    nom: str
    metier: str
    url: str
    remarque: str = ""
    page_carrieres: str = ""
    logiciel: str = ""
    cas: str = ""
    balisage: str = ""
    robots: str = ""
    conditions: str = ""
    conditions_url: str = ""
    conditions_phrase: str = ""
    offres_lues: int = 0
    offres_vaud: str = ""
    verdict: str = ""
    raison: str = ""
    raison_balisage: str = ""
    exemples: list[str] = field(default_factory=list)


def find_list_page(start: Page, web: Polite) -> tuple[Page, list[str], list[dict[str, object]]]:
    """Depuis la page de départ, suit au plus MAX_HOPS liens jusqu'à une page qui montre des offres."""
    page, visited = start, {start.url.rstrip("/")}
    for _hop in range(MAX_HOPS + 1):
        found = postings(page.text)
        offers = offer_links(page)
        name, _case = platform(page.url)
        if found or offers or name:
            return page, offers, found
        for url in next_pages(page):
            if url.rstrip("/") in visited:
                continue
            visited.add(url.rstrip("/"))
            if not web.allowed(url):
                continue  # jamais demandée ; la page de départ et les offres, elles, arrêtent la lecture
            nxt = web.get(url)
            if nxt is not None and nxt.status == 200:
                page = nxt
                break
        else:
            break
    return page, offer_links(page), postings(page.text)


def sitemap_offers(page: Page, web: Polite) -> list[str]:
    """Les pages d'offres annoncées par le plan du site, quand la liste est dessinée en JavaScript."""
    host = web.host(page.url)
    web.rules(page.url)
    queue = list(web.sitemaps.get(host, []))[:3] or [host + "/sitemap.xml"]
    found: list[str] = []
    for _ in range(6):
        if not queue:
            break
        sitemap = web.get(queue.pop(0))
        if sitemap is None or sitemap.status != 200:
            continue
        for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sitemap.text):
            loc = html.unescape(loc)
            if loc.endswith(".xml") or ".xml?" in loc:
                if re.search(r"job|career|stelle|emploi|offre|posting", loc, re.I):
                    queue.insert(0, loc)
                else:
                    queue.append(loc)
            elif is_offer(loc) and loc not in found:
                found.append(loc)
        if len(found) >= MAX_OFFERS:
            break
    return found


def inspect(employer: Employer, web: Polite) -> Employer:
    rules = web.rules(employer.url)
    if rules is None:
        return verdict(employer, robots="injoignable", raison="robots.txt injoignable (site en panne ?)", check=True)
    state = web.robots_state.get(web.host(employer.url), "")
    if not web.allowed(employer.url):
        return verdict(employer, robots="interdit", raison="robots.txt interdit la page carrières")
    employer.robots = "absent" if state == "absent" else "autorisé"

    start = web.get(employer.url)
    if start is None or start.status != 200:
        status = start.status if start else "?"
        return verdict(employer, raison=f"page de départ en erreur (HTTP {status})", check=True)
    terms = terms_link(start)

    page, offers, found = find_list_page(start, web)
    employer.page_carrieres = page.url
    if page is not start and not terms:
        terms = terms_link(page)
    employer.logiciel, case = platform(page.url, *[u for u, _ in links(page)])
    employer.cas = case

    places: list[tuple[str, str, str]] = []
    marked: list[bool] = []
    account = feed_account(employer.logiciel, page.url, *[u for u, _ in links(page)]) if case == "1" else None
    if account:
        _pattern, url_of, parse = FEEDS[employer.logiciel]
        if not web.allowed(url_of(account)):
            return verdict(employer, robots="ambigu", raison=f"robots.txt interdit le flux {employer.logiciel}", check=True)
        feed = web.get(url_of(account))
        if feed is not None and feed.status == 200:
            places = parse(feed.text)
            employer.balisage = f"flux {employer.logiciel}"
    if not employer.balisage:
        for posting in found:
            places.append((str(posting.get("title", "")), *posting_place(posting)))
            marked.append(complete(posting))
        if not found and not offers:
            offers = sitemap_offers(page, web)
        for url in offers[:MAX_OFFERS] if not found else []:
            if not web.allowed(url):
                # Arrêt immédiat : la liste est permise mais pas les offres.
                return verdict(employer, robots="ambigu", raison=f"robots.txt interdit les pages d'offres ({url})", check=True)
            detail = web.get(url)
            if detail is None or detail.status != 200:
                continue
            if not employer.logiciel:
                employer.logiciel, employer.cas = platform(detail.url)
            items = postings(detail.text)
            if items:
                places.append((str(items[0].get("title", "")), *posting_place(items[0])))
                marked.append(complete(items[0]))
            else:
                marked.append(False)
        if marked and all(marked):
            employer.balisage = "oui"
        elif any(marked) or places:
            employer.balisage = "partiel"
        else:
            employer.balisage = "non"
            if not offers and not found:
                employer.raison_balisage = (
                    "offres affichées par JavaScript" if employer.logiciel == "Workday"
                    else "aucune offre lisible dans la page ni dans le plan du site (affichage par JavaScript ?)"
                )

    employer.offres_lues = len(places) if places else len(marked)
    vaud = [f"{t} ({p.strip()})" for t, p, c in places if in_vaud(p, c)]
    capped = not employer.balisage.startswith("flux") and len(offers) > MAX_OFFERS
    employer.offres_vaud = (f"≥{len(vaud)}" if capped else str(len(vaud))) if places else "?"
    employer.exemples = vaud[:3]

    if terms:
        employer.conditions_url = terms
        terms_page = web.get(terms)
        if terms_page is None:
            employer.conditions = "page interdite par robots.txt"
        elif terms_page.status == 200:
            employer.conditions, employer.conditions_phrase = terms_verdict(terms_page.text)
        else:
            employer.conditions = f"page en erreur (HTTP {terms_page.status})"
    else:
        employer.conditions = "pas de page trouvée"
    return verdict(employer)


LISIBLE, NON_LISIBLE, A_VERIFIER = "lisible", "non lisible", "à vérifier à la main"


def verdict(employer: Employer, robots: str = "", raison: str = "", check: bool = False) -> Employer:
    """Trois verdicts (décision du 13.11.2026) :

    - non lisible : ni balisage complet ni flux public, ou robots.txt interdit la page carrières,
      ou les conditions interdisent la lecture automatique ;
    - à vérifier à la main : conditions introuvables ou illisibles, robots.txt injoignable ou qui
      permet la liste mais pas les offres, page de départ en erreur ;
    - lisible : tout le reste, c'est-à-dire balisage complet ou flux, robots.txt et conditions qui le permettent.
    """
    if robots:
        employer.robots = robots
    if raison:
        employer.verdict = A_VERIFIER if check else NON_LISIBLE
        employer.raison = raison
        return employer
    blocking, to_check = [], []
    if not (employer.balisage == "oui" or employer.balisage.startswith("flux")):
        what = employer.raison_balisage or {
            "partiel": "balisage JobPosting incomplet (titre, lieu ou date manquant)",
            "non": "pas de balisage JobPosting ni de flux public",
        }.get(employer.balisage, "balisage inconnu")
        if employer.logiciel and employer.logiciel not in what:
            what += f" ; logiciel {employer.logiciel}"
        blocking.append(what)
    if employer.conditions == "interdite":
        blocking.append("les conditions interdisent la lecture automatique (phrase à relire)")
    elif employer.conditions not in ("rien", "permise"):
        to_check.append(f"conditions à vérifier ({employer.conditions})")
    if blocking:
        employer.verdict, employer.raison = NON_LISIBLE, " ; ".join(blocking + to_check)
    elif to_check:
        employer.verdict, employer.raison = A_VERIFIER, " ; ".join(to_check)
    else:
        employer.verdict = LISIBLE
        employer.raison = f"{employer.balisage} ; robots.txt {employer.robots} ; conditions : {employer.conditions}"
    return employer


def read_employers(path: Path) -> list[Employer]:
    with path.open(encoding="utf-8") as handle:
        return [Employer(row["nom"], row["metier"], row["url"], row.get("remarque") or "") for row in csv.DictReader(handle)]


def metiers(employer: Employer) -> list[str]:
    return [m.strip() for m in employer.metier.split(";") if m.strip()]


def _share(part: int, whole: int) -> str:
    return f"{part / whole:.0%}" if whole else "—"


def summary(employers: list[Employer]) -> list[str]:
    total = len(employers)
    readable = sum(1 for e in employers if e.verdict == LISIBLE)
    check = sum(1 for e in employers if e.verdict == A_VERIFIER)
    strict = readable / total if total else 0
    provisional_base = total - check
    provisional = readable / provisional_base if provisional_base else 0
    lines = [
        f"- Employeurs testés : **{total}** ; lisibles : {readable} ; non lisibles : {total - readable - check} ; "
        f"à vérifier à la main : {check}.",
        f"- **Strict** (les « à vérifier » comptent comme non lisibles) : {readable} sur {total} = "
        f"**{_share(readable, total)}** ({'au-dessus' if strict >= THRESHOLD else 'en dessous'} du seuil de 50 %).",
        f"- **Provisoire** (les « à vérifier » sont exclus) : {readable} sur {provisional_base} = "
        f"**{_share(readable, provisional_base)}** ({'au-dessus' if provisional >= THRESHOLD else 'en dessous'} du seuil de 50 %).",
        "- Le chiffre final se compare au seuil après la vérification à la main des lignes « à vérifier ».",
    ]
    for metier in sorted({m for e in employers for m in metiers(e)}):
        group = [e for e in employers if metier in metiers(e)]
        ok = sum(1 for e in group if e.verdict == LISIBLE)
        tc = sum(1 for e in group if e.verdict == A_VERIFIER)
        lines.append(f"- {metier} : {ok} lisibles sur {len(group)} employeurs ({tc} à vérifier)")
    case3 = [e.nom for e in employers if e.cas == "3"]
    lines.append(
        f"- Logiciel sans flux public (SuccessFactors, Refline, Abacus/umantis, Prospective) : {len(case3)} sur {total}"
        + (f" ({', '.join(case3)})" if case3 else "")
    )
    return lines


def cell(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def write(employers: list[Employer], folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "inventaire.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(employers[0])))
        writer.writeheader()
        for e in employers:
            row = asdict(e)
            row["exemples"] = " ; ".join(e.exemples)
            writer.writerow(row)
    columns = ["Employeur", "Métier", "Page carrière", "Balisage", "robots.txt", "Conditions",
               "Offres en Vaud ce jour", "Verdict", "Raison"]
    lines = [
        "# Inventaire des pages carrières (Vaud)",
        "",
        f"Lu le {time.strftime('%Y-%m-%d')} par `scripts/inventaire_employeurs.py`. Définition de « lisible » et seuil : docs/145 §2.",
        "",
        *summary(employers),
        "",
        "| " + " | ".join(columns) + " |",
        "|" + "---|" * len(columns),
    ]
    for e in employers:
        conditions = e.conditions + (f" ([page]({e.conditions_url}))" if e.conditions_url else "")
        if e.conditions_phrase:
            conditions += f" : « {e.conditions_phrase} »"
        page = f"[lien]({e.page_carrieres})" if e.page_carrieres else ""
        if e.logiciel:
            page += f" ({e.logiciel})"
        raison = e.raison + (f" ; {e.remarque}" if e.remarque else "")
        row = [e.nom, e.metier.replace(";", ", "), page, e.balisage, e.robots, conditions, e.offres_vaud, e.verdict, raison]
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    lines += [
        "",
        "Verdicts : « lisible », « non lisible », « à vérifier à la main » (définitions : docs/145 §2).",
        "« Offres en Vaud ce jour » : offres lues ce jour-là dont le lieu est une localité vaudoise ;",
        f"« ≥ » quand la page en montrait plus de {MAX_OFFERS} (on n'en lit pas davantage) ; « ? » quand aucun lieu n'a pu être lu.",
    ]
    out = folder / "inventaire.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", type=Path, default=FOLDER / "employeurs-vaud.csv")
    parser.add_argument("--sortie", type=Path, default=FOLDER)
    parser.add_argument("--contact", help="adresse e-mail ajoutée au nom du robot (conseillé)")
    args = parser.parse_args(argv)
    global USER_AGENT
    if args.contact:
        USER_AGENT = f"jobA1-inventaire/1.1 (+https://joba1.ch; {args.contact})"
    web = Polite()
    employers = []
    for employer in read_employers(args.csv):
        print(f"… {employer.nom}", flush=True)
        employers.append(inspect(employer, web))
    out = write(employers, args.sortie)
    print("\n".join(summary(employers)))
    print(out)


if __name__ == "__main__":
    main()
