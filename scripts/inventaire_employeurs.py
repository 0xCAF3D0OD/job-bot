"""Inventaire des pages carrières d'employeurs vaudois (docs/145, étape 1).

Le script ne touche ni à l'app ni à la base : il lit des pages publiques et écrit deux tableaux.

    # Liste 1 : les employeurs de docs/inventaire-employeurs/employeurs-vaud.csv
    python3 scripts/inventaire_employeurs.py liste1

    # Liste 2 : les entreprises qui ont un flux public (Personio, Greenhouse, Lever, Recruitee,
    # Workable, SmartRecruiters, Ashby) avec au moins une offre en Vaud, trouvées par l'index
    # public de Common Crawl. Long (plusieurs heures) ; reprend là où il s'est arrêté.
    python3 scripts/inventaire_employeurs.py liste2 [--max-par-plateforme N]

Règles suivies : robots.txt lu avant toute page (refus = la page n'est pas lue), `Crawl-delay`
respecté (2 s au moins entre deux pages d'un même site), un robot qui se nomme, une seule
lecture par page. Rien de personnel n'est lu ni gardé : seulement des noms d'employeurs,
des titres d'offres et des lieux.

La colonne « conditions » est une proposition : le script cherche dans la page des conditions
d'utilisation une phrase sur les robots ou l'extraction automatique. Chaque « interdite » et
chaque « permise » se relit à la main avant d'utiliser le site.

Seulement la bibliothèque standard de Python (3.11 ou plus), pour tourner sur n'importe quel Mac.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "docs" / "inventaire-employeurs"
USER_AGENT = "jobA1-inventaire/1.0 (+https://joba1.ch)"
MIN_DELAY = 2.0
TIMEOUT = 20
MAX_BYTES = 3_000_000


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
                self.robots[host] = None
                return None
            if page.status in (401, 403):
                parser.disallow_all = True
            elif page.status >= 400:
                parser.allow_all = True
            else:
                parser.parse(page.text.splitlines())
                self.sitemaps[host] = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", page.text)
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

# (nom, cas, motif dans les liens ou le code de la page). Cas 1 = flux public fait pour être
# lu ; cas 3 = logiciel courant en Suisse sans flux public ; « autre » = connu, sans cas fixé.
PLATFORMS: list[tuple[str, str, re.Pattern[str]]] = [
    ("Personio", "1", re.compile(r"[\w-]+\.jobs\.personio\.(?:de|com)", re.I)),
    ("Greenhouse", "1", re.compile(r"(?:job-)?boards(?:-api)?\.greenhouse\.io", re.I)),
    ("Lever", "1", re.compile(r"jobs\.lever\.co|api\.lever\.co", re.I)),
    ("Recruitee", "1", re.compile(r"[\w-]+\.recruitee\.com", re.I)),
    ("Workable", "1", re.compile(r"apply\.workable\.com", re.I)),
    ("SmartRecruiters", "1", re.compile(r"(?:jobs|careers|api)\.smartrecruiters\.com", re.I)),
    ("Ashby", "1", re.compile(r"jobs\.ashbyhq\.com|api\.ashbyhq\.com", re.I)),
    ("SuccessFactors", "3", re.compile(r"successfactors|sapsf\.|jobs\.sap\.com|career\d*\.sap|rmkcdn", re.I)),
    ("Refline", "3", re.compile(r"refline\.ch", re.I)),
    ("Abacus / umantis", "3", re.compile(r"umantis\.com|abacuscity|abacus\.ch/.*recruit", re.I)),
    ("Prospective", "3", re.compile(r"prospective\.ch|jobs\.prospective", re.I)),
    ("Workday", "autre", re.compile(r"myworkdayjobs\.com|wd\d\.myworkday", re.I)),
    ("Teamtailor", "autre", re.compile(r"teamtailor\.com", re.I)),
    ("Softgarden", "autre", re.compile(r"softgarden\.io", re.I)),
    ("Taleo", "autre", re.compile(r"taleo\.net", re.I)),
    ("Jobcloud (jobs.ch, jobup)", "autre", re.compile(r"jobs\.ch/|jobup\.ch/", re.I)),
]

LD_JSON = re.compile(r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", re.S | re.I)
LINK = re.compile(r"<a\b[^>]*href=[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", re.S | re.I)
CAREER = re.compile(r"carri[eè]re|emploi|offres?-d|postes?-vacant|jobs?\b|karriere|stellen|careers?|recrutement", re.I)
OFFER = re.compile(r"/(?:job|jobs|emploi|offre|offres|poste|stelle|stellen|vacanc|position|career)s?/[^/?#]{4,}", re.I)
TERMS = re.compile(
    r"conditions[-_ ]g[eé]n[eé]rales|conditions[-_ ]d.utilisation|\bcgu\b|mentions?[-_ ]l[eé]gales|"
    r"nutzungsbedingungen|terms|rechtliche|disclaimer|informations?[-_ ]juridiques|legal",
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


def postings(page: str) -> int:
    """Le nombre de `JobPosting` (schema.org) dans les blocs JSON-LD de la page."""
    count = 0
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
                    count += 1
                stack.extend(v for v in item.values() if isinstance(v, (list, dict)))
    return count


def links(page: Page) -> list[tuple[str, str]]:
    found = []
    for href, label in LINK.findall(page.text):
        url = urllib.parse.urljoin(page.url, html.unescape(href.strip()))
        if url.startswith("http"):
            found.append((url, plain(label)))
    return found


def career_link(page: Page) -> str | None:
    for url, label in links(page):
        if CAREER.search(label) or CAREER.search(urllib.parse.urlsplit(url).path):
            if url.rstrip("/") != page.url.rstrip("/"):
                return url
    return None


def offer_link(page: Page) -> str | None:
    for url, _label in links(page):
        if OFFER.search(urllib.parse.urlsplit(url).path):
            return url
    return None


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


# --- Liste 1 : les employeurs choisis ----------------------------------------------------


@dataclass
class Employer:
    nom: str
    metier: str
    url: str
    page_carrieres: str = ""
    robots: str = ""
    crawl_delay: str = ""
    sitemap: str = ""
    logiciel: str = ""
    cas: str = ""
    jobposting: int = 0
    conditions: str = ""
    conditions_url: str = ""
    conditions_phrase: str = ""
    remarque: str = ""


def inspect(employer: Employer, web: Polite) -> Employer:
    rules = web.rules(employer.url)
    if rules is None:
        employer.robots, employer.cas, employer.remarque = "injoignable", "erreur", "site injoignable"
        return employer
    employer.robots = "permis" if web.allowed(employer.url) else "interdit"
    employer.crawl_delay = str(rules.crawl_delay(USER_AGENT) or "")
    employer.sitemap = "oui" if web.sitemaps.get(web.host(employer.url)) else "non"
    home = web.get(employer.url)
    if home is None:
        employer.cas = "robots.txt interdit"
        return employer
    if home.status != 200:
        employer.cas, employer.remarque = "erreur", f"HTTP {home.status}"
        return employer

    terms = terms_link(home)
    page = home
    if not CAREER.search(urllib.parse.urlsplit(home.url).path):
        target = career_link(home)
        if target:
            page = web.get(target) or home
    employer.page_carrieres = page.url

    # Le logiciel se voit dans l'adresse, les liens ou un cadre intégré de la page carrières.
    employer.logiciel, case = platform(page.url, page.text)
    count = postings(page.text)
    if not count:
        offer = offer_link(page)
        if offer:
            detail = web.get(offer)
            if detail is not None and detail.status == 200:
                count = postings(detail.text)
                if not employer.logiciel:
                    employer.logiciel, case = platform(detail.url, detail.text)
    employer.jobposting = count
    if case == "1":
        employer.cas = "1"
    elif count:
        employer.cas = "2"
    elif case == "3":
        employer.cas = "3"
    else:
        employer.cas = "inconnu"

    if terms:
        employer.conditions_url = terms
        terms_page = web.get(terms)
        if terms_page is None:
            employer.conditions = "page interdite par robots.txt"
        elif terms_page.status == 200:
            employer.conditions, employer.conditions_phrase = terms_verdict(terms_page.text)
        else:
            employer.conditions = f"HTTP {terms_page.status}"
    else:
        employer.conditions = "pas de page trouvée"
    return employer


def read_employers(path: Path) -> list[Employer]:
    with path.open(encoding="utf-8") as handle:
        return [Employer(row["nom"], row["metier"], row["url"]) for row in csv.DictReader(handle)]


def summary(employers: list[Employer]) -> list[str]:
    total = len(employers)
    by_case = Counter(e.cas for e in employers)
    case3_software = sum(1 for e in employers if platform_case(e.logiciel) == "3")
    lines = [f"- {total} employeurs lus."]
    for case in ("1", "2", "3", "inconnu", "robots.txt interdit", "erreur"):
        if by_case.get(case):
            lines.append(f"- cas {case} : {by_case[case]} ({by_case[case] * 100 // total} %)")
    lines.append(
        f"- logiciel du cas 3 (SuccessFactors, Refline, Abacus/umantis, Prospective), même avec JobPosting : "
        f"{case3_software} ({case3_software * 100 // max(total, 1)} %)"
    )
    for metier in sorted({e.metier for e in employers}):
        group = [e for e in employers if e.metier == metier]
        n3 = sum(1 for e in group if platform_case(e.logiciel) == "3")
        lines.append(f"- {metier} : {len(group)} employeurs, dont {n3} sur un logiciel du cas 3")
    return lines


def platform_case(name: str) -> str:
    return next((case for n, case, _ in PLATFORMS if n == name), "")


def cell(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def write_liste1(employers: list[Employer], folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "liste1.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(employers[0])))
        writer.writeheader()
        writer.writerows(asdict(e) for e in employers)
    columns = ["Employeur", "Métier", "Cas", "Logiciel", "JobPosting", "robots.txt", "Crawl-delay", "Conditions", "Page"]
    lines = [
        "# Liste 1 : employeurs vaudois choisis",
        "",
        f"Lu le {time.strftime('%Y-%m-%d')} par `scripts/inventaire_employeurs.py liste1`.",
        "",
        *summary(employers),
        "",
        "| " + " | ".join(columns) + " |",
        "|" + "---|" * len(columns),
    ]
    for e in employers:
        conditions = e.conditions + (f" ([page]({e.conditions_url}))" if e.conditions_url else "")
        row = [e.nom, e.metier, e.cas, e.logiciel, e.jobposting, e.robots, e.crawl_delay, conditions, e.page_carrieres]
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    phrases = [e for e in employers if e.conditions_phrase]
    if phrases:
        lines += ["", "## Phrases trouvées dans les conditions (à relire)", ""]
        lines += [f"- **{e.nom}** ({e.conditions}) : « {e.conditions_phrase} »" for e in phrases]
    out = folder / "liste1.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# --- Liste 2 : à l'envers, depuis les flux publics ---------------------------------------


@dataclass
class Feed:
    name: str
    cdx: list[str]  # motifs d'adresse pour l'index de Common Crawl
    slug: Callable[[str], str | None]
    url: Callable[[str], str]
    parse: Callable[[str], list[tuple[str, str, str]]]  # (titre, lieu, pays)


def _host_slug(suffix: str, exclude: set[str]) -> Callable[[str], str | None]:
    def slug(url: str) -> str | None:
        host = urllib.parse.urlsplit(url).netloc.lower().split(":")[0]
        if host.endswith(suffix):
            name = host[: -len(suffix)].rstrip(".")
            if name and "." not in name and name not in exclude:
                return name
        return None

    return slug


def _path_slug(exclude: set[str]) -> Callable[[str], str | None]:
    def slug(url: str) -> str | None:
        parts = [p for p in urllib.parse.urlsplit(url).path.split("/") if p]
        if parts and parts[0].lower() not in exclude and re.fullmatch(r"[\w.-]{2,80}", parts[0]):
            return parts[0]
        return None

    return slug


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
        title = position.findtext("name") or ""
        offices = [position.findtext("office") or ""]
        offices += [o.text or "" for o in position.iter("additionalOffice")]
        found.append((title, " / ".join(o for o in offices if o), ""))
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


FEEDS = [
    Feed("Personio", ["*.jobs.personio.de", "*.jobs.personio.com"],
         lambda u: _host_slug(".jobs.personio.de", set())(u) or _host_slug(".jobs.personio.com", set())(u),
         lambda s: f"https://{s}.jobs.personio.de/xml?language=fr", parse_personio),
    Feed("Greenhouse", ["boards.greenhouse.io/*", "job-boards.greenhouse.io/*"],
         _path_slug({"embed", "v1"}), lambda s: f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs", parse_greenhouse),
    Feed("Lever", ["jobs.lever.co/*"], _path_slug(set()),
         lambda s: f"https://api.lever.co/v0/postings/{s}?mode=json", parse_lever),
    Feed("Recruitee", ["*.recruitee.com"], _host_slug(".recruitee.com", {"www", "app", "api", "careers", "blog", "support", "docs"}),
         lambda s: f"https://{s}.recruitee.com/api/offers/", parse_recruitee),
    Feed("Workable", ["apply.workable.com/*"], _path_slug({"api", "j", "careers"}),
         lambda s: f"https://apply.workable.com/api/v1/widget/accounts/{s}", parse_workable),
    Feed("SmartRecruiters", ["jobs.smartrecruiters.com/*"], _path_slug({"oneclick-ui", "sr-jobs", "ni", "static"}),
         lambda s: f"https://api.smartrecruiters.com/v1/companies/{s}/postings", parse_smartrecruiters),
    Feed("Ashby", ["jobs.ashbyhq.com/*"], _path_slug({"api"}),
         lambda s: f"https://api.ashbyhq.com/posting-api/job-board/{s}", parse_ashby),
]

# Les localités vaudoises les plus courantes dans les offres. « VD », « Vaud », « Waadt »
# comptent aussi. Un lieu hors de Suisse (pays donné par le flux) est écarté.
VAUD_TOWNS = """
lausanne renens prilly pully lutry epalinges ecublens crissier bussigny chavannes-pres-renens saint-sulpice
le mont-sur-lausanne romanel-sur-lausanne cheseaux-sur-lausanne belmont-sur-lausanne paudex savigny
morges preverenges tolochenaz saint-prex etoy allaman aubonne rolle gland nyon prangins eysins coppet founex
commugny mies tannay crans-pres-celigny cossonay penthalaz echallens yverdon-les-bains yverdon grandson orbe
vallorbe sainte-croix le sentier le chenit l'abbaye le brassus vevey corseaux corsier-sur-vevey la tour-de-peilz
blonay saint-legier montreux clarens villeneuve chexbres puidoux oron moudon lucens payerne avenches aigle
bex ollon villars-sur-ollon leysin chateau-d'oex villars-sainte-croix mex vufflens-la-ville apples bière biere
""".split()
VAUD_EXTRA = ["vaud", "waadt", "canton de vaud"]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[’`]", "'", text)


_VAUD = re.compile(
    r"(?<![\w-])(?:" + "|".join(re.escape(t) for t in sorted(VAUD_TOWNS + VAUD_EXTRA, key=len, reverse=True)) + r")(?![\w-])"
    r"|\(vd\)|,\s*vd\b|\bvd,|\bvd\s*$|\bch-vd\b"
)


def in_vaud(place: str, country: str = "") -> bool:
    if country and normalize(country) not in {"ch", "che", "switzerland", "suisse", "schweiz", "svizzera"}:
        return False
    return bool(_VAUD.search(normalize(place)))


def cdx_slugs(feed: Feed, web_get: Callable[[str], str], crawl: str, max_pages: int | None) -> set[str]:
    """Les comptes d'une plateforme vus dans l'index public de Common Crawl."""
    slugs: set[str] = set()
    base = f"https://index.commoncrawl.org/{crawl}-index"
    for pattern in feed.cdx:
        query = urllib.parse.urlencode({"url": pattern, "output": "json", "fl": "url", "showNumPages": "true"})
        info = _json(web_get(f"{base}?{query}"))
        pages = int(info.get("pages", 0)) if isinstance(info, dict) else 0
        for number in range(min(pages, max_pages) if max_pages else pages):
            query = urllib.parse.urlencode({"url": pattern, "output": "json", "fl": "url", "page": number})
            for line in web_get(f"{base}?{query}").splitlines():
                row = _json(line)
                if isinstance(row, dict) and (slug := feed.slug(row.get("url", ""))):
                    slugs.add(slug)
    return slugs


def liste2(web: Polite, folder: Path, max_per_platform: int | None, cdx_pages: int | None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    cache_path = folder / "liste2-cache.json"
    cache: dict[str, dict[str, object]] = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    lock = threading.Lock()

    def text_of(url: str) -> str:
        page = web.get(url)
        return page.text if page and page.status == 200 else ""

    crawls = _json(text_of("https://index.commoncrawl.org/collinfo.json"))
    if not isinstance(crawls, list) or not crawls:
        sys.exit("Index de Common Crawl injoignable (ou interdit par son robots.txt).")
    crawl = crawls[0]["id"]

    def run(feed: Feed) -> None:
        slugs = sorted(cdx_slugs(feed, text_of, crawl, cdx_pages))
        if max_per_platform:
            slugs = slugs[:max_per_platform]
        print(f"{feed.name} : {len(slugs)} comptes à lire", flush=True)
        for index, slug in enumerate(slugs, 1):
            key = f"{feed.name}:{slug}"
            if key in cache:
                continue
            if feed.cdx[0].startswith("*."):
                # Un sous-domaine par entreprise : le délai par site ne protège pas la plateforme.
                web.sleep(MIN_DELAY)
            url = feed.url(slug)
            page = web.get(url)
            jobs = feed.parse(page.text) if page and page.status == 200 else []
            vaud = [(t, p) for t, p, c in jobs if in_vaud(p, c)]
            entry = {"plateforme": feed.name, "compte": slug, "flux": url, "offres": len(jobs),
                     "vaud": len(vaud), "exemples": [f"{t} ({p.strip()})" for t, p in vaud[:3]],
                     "statut": page.status if page else "robots.txt"}
            with lock:
                cache[key] = entry
                if index % 25 == 0:
                    cache_path.write_text(json.dumps(cache, ensure_ascii=False))

    threads = [threading.Thread(target=run, args=(feed,)) for feed in FEEDS]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    cache_path.write_text(json.dumps(cache, ensure_ascii=False))

    rows = sorted((e for e in cache.values() if int(e["vaud"]) > 0), key=lambda e: -int(e["vaud"]))
    read = Counter(str(e["plateforme"]) for e in cache.values())
    found = Counter(str(e["plateforme"]) for e in rows)
    lines = [
        "# Liste 2 : entreprises avec un flux public et des offres en Vaud",
        "",
        f"Lu le {time.strftime('%Y-%m-%d')} par `scripts/inventaire_employeurs.py liste2` (index Common Crawl {crawl}).",
        "",
        *[f"- {name} : {read[name]} comptes lus, {found[name]} avec au moins une offre en Vaud" for name in sorted(read)],
        "",
        "| Compte | Plateforme | Offres en Vaud | Offres en tout | Exemples | Flux |",
        "|---|---|---|---|---|---|",
    ]
    for e in rows:
        lines.append(
            f"| {cell(e['compte'])} | {e['plateforme']} | {e['vaud']} | {e['offres']} | "
            f"{cell('; '.join(e['exemples']))} | {e['flux']} |"  # type: ignore[arg-type]
        )
    out = folder / "liste2.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="liste", required=True)
    one = sub.add_parser("liste1", help="les employeurs du fichier CSV")
    one.add_argument("--csv", type=Path, default=FOLDER / "employeurs-vaud.csv")
    two = sub.add_parser("liste2", help="les flux publics avec des offres en Vaud")
    two.add_argument("--max-par-plateforme", type=int, default=None)
    two.add_argument("--pages-index", type=int, default=None, help="pages de l'index lues par motif (toutes par défaut)")
    for p in (one, two):
        p.add_argument("--sortie", type=Path, default=FOLDER)
    args = parser.parse_args(argv)

    web = Polite()
    if args.liste == "liste1":
        employers = []
        for employer in read_employers(args.csv):
            print(f"… {employer.nom}", flush=True)
            employers.append(inspect(employer, web))
        print(write_liste1(employers, args.sortie))
    else:
        print(liste2(web, args.sortie, args.max_par_plateforme, args.pages_index))


if __name__ == "__main__":
    main()
