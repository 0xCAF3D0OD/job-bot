"""Les premières offres par la recherche web de l'IA (docs/104, « Premières offres par le web »).

jobA1 n'ouvre aucune page d'annonce et ne lit aucun site d'emploi : il demande une recherche
web à l'IA (l'outil déjà utilisé pour les adresses et les formations) et n'en garde que
l'intitulé, l'entreprise et le lieu quand le résultat les montre, et le lien. Chaque lien est
vérifié contre ceux que le moteur a réellement rendus : un lien que l'IA aurait inventé est
écarté. L'intitulé, l'entreprise et le lieu sont des morceaux du titre rendu par le moteur,
recopiés par le code : l'IA choisit, elle ne reformule pas. Un résultat daté de plus de
14 jours est écarté ; sans date connue, il est gardé. Ces offres ne sont ni lues ni notées
(pas de texte d'annonce).
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from importlib import resources
from typing import Any
from urllib.parse import urlsplit

from jobbot.db.models import WEB_LINK_SOURCE
from jobbot.llm.client import RawResult, WebResult
from jobbot.sources.base import RawOffer

PROMPT_VERSION = "first-offers-web-v1"
INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath("prompts/first-offers-web-v1.md").read_text("utf-8")
)
LINK_SOURCE = WEB_LINK_SOURCE
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 4_000
MAX_SEARCHES = 2
MAX_OFFERS = 10
# Deux recherches web (0,01 USD chacune) et les résultats lus par un petit modèle.
ESTIMATE_USD = Decimal("0.06")
# La réponse, éventuellement dans un bloc de code (« ```json … ``` »).
_ANSWER = re.compile(r"<reponse>\s*(?:```(?:json)?\s*)?(\{.*\})\s*(?:```\s*)?</reponse>", re.S)
# Un titre qui n'est qu'un identifiant (« 61d4c807 8a3c 4113 9b3a 6791d579b573 »).
_CODE = re.compile(r"^[0-9a-f]{8}[ -]?([0-9a-f]{4}[ -]?){3}[0-9a-f]{12}$", re.I)


def request_params(terms: str, location: str | None, model: str = MODEL) -> dict[str, Any]:
    def clean(value: str) -> str:
        return " ".join(value.replace("<", " ").replace(">", " ").split())[:150]

    content = f"<metier>{clean(terms)}</metier>\n<lieu>{clean(location or 'Suisse romande')}</lieu>"
    return {
        "model": model,
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
        # Pas de format JSON imposé : incompatible avec les citations de la recherche web.
    }


def _same(url: str) -> str:
    """Une adresse sans son fragment ni sa barre finale, pour la comparer à celles du moteur."""
    parts = urlsplit(url.strip())
    return f"{parts.scheme}://{parts.netloc.lower()}{parts.path.rstrip('/')}?{parts.query}"


MAX_AGE = timedelta(days=14)
_MONTHS = {
    name: number
    for number, names in enumerate(
        (
            ("january", "jan", "janvier", "janv"),
            ("february", "feb", "février", "fevrier", "févr", "fevr"),
            ("march", "mar", "mars"),
            ("april", "apr", "avril", "avr"),
            ("may", "mai"),
            ("june", "jun", "juin"),
            ("july", "jul", "juillet", "juil"),
            ("august", "aug", "août", "aout"),
            ("september", "sep", "sept", "septembre"),
            ("october", "oct", "octobre"),
            ("november", "nov", "novembre"),
            ("december", "dec", "décembre", "decembre", "déc"),
        ),
        start=1,
    )
    for name in names
}
_UNITS = {
    "minute": 0, "hour": 0, "heure": 0, "day": 1, "jour": 1, "week": 7, "semaine": 7,
    "month": 30, "mois": 30, "year": 365, "an": 365,
}  # fmt: skip
_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_MONTH_FIRST = re.compile(r"([^\W\d]+)\.? (\d{1,2}),? (\d{4})")
_DAY_FIRST = re.compile(r"(\d{1,2})(?:er)? ([^\W\d]+)\.? (\d{4})")
_AGO = re.compile(r"(?:il y a )?(\d+) ([^\W\d]+)(?: ago)?")


def page_date(page_age: str | None, today: date) -> date | None:
    """La date d'un résultat, d'après l'âge de page rendu par le moteur (« November 3, 2026 »,
    « 2026-11-03 », « 3 days ago »). `None` quand il n'y en a pas ou qu'elle est illisible."""
    value = " ".join((page_age or "").lower().split())
    if not value:
        return None
    try:
        if match := _ISO.match(value):
            return date(int(match[1]), int(match[2]), int(match[3]))
        if (match := _MONTH_FIRST.fullmatch(value)) and match[1] in _MONTHS:
            return date(int(match[3]), _MONTHS[match[1]], int(match[2]))
        if (match := _DAY_FIRST.fullmatch(value)) and match[2] in _MONTHS:
            return date(int(match[3]), _MONTHS[match[2]], int(match[1]))
    except ValueError:
        return None
    if value in ("today", "aujourd'hui"):
        return today
    if value in ("yesterday", "hier"):
        return today - timedelta(days=1)
    if match := _AGO.fullmatch(value):
        days = _UNITS.get(match[2], _UNITS.get(match[2].removesuffix("s")))
        if days is not None:
            return today - timedelta(days=int(match[1]) * days)
    return None


def _squash(value: str) -> str:
    return " ".join(value.split())


def verbatim(wanted: str | None, shown: str) -> str | None:
    """Le morceau du titre rendu par le moteur qui correspond à ce que l'IA propose, recopié
    depuis ce titre. `None` si la proposition n'y figure pas mot pour mot (à la casse près)."""
    wanted = _squash(wanted) if isinstance(wanted, str) else ""
    if not wanted:
        return None
    start = shown.casefold().find(wanted.casefold())
    if start < 0 or len(shown.casefold()) != len(shown):
        return wanted if wanted in shown else None
    return shown[start : start + len(wanted)]


# Les motifs d'écart, affichés par la commande d'essai.
KEPT = "gardée"
TOO_OLD = "datée de plus de 14 jours"
OVER_LIMIT = "au-delà de 10 offres"
NOT_PROPOSED = "non retenue par l'IA"
UNKNOWN_LINK = "lien absent des résultats du moteur"
BAD_LINK = "lien sans https ou page d'accueil"
NO_TITLE = "le moteur ne donne pas de titre"
CODE_TITLE = "titre réduit à un identifiant"


@dataclass(frozen=True)
class Verdict:
    """Ce qu'il advient d'un résultat du moteur, ou d'un lien proposé par l'IA hors résultats."""

    url: str
    title: str
    page_age: str | None
    reason: str


@dataclass
class Selection:
    """Ce que la recherche a rendu et ce qui en est gardé (affiché par la commande d'essai)."""

    offers: list[RawOffer] = field(default_factory=list)
    results: int = 0  # résultats rendus par le moteur
    dated: int = 0  # dont ceux qui portent une date lisible
    proposed: int = 0  # offres proposées par l'IA dont le lien vient bien du moteur
    too_old: int = 0  # écartées : datées de plus de 14 jours
    undated_kept: int = 0  # gardées sans date connue
    # Un verdict par résultat du moteur, dans son ordre, puis les liens inconnus de l'IA.
    verdicts: list[Verdict] = field(default_factory=list)
    # Pourquoi la réponse de l'IA n'a pas pu être lue (None : elle a été lue).
    problem: str | None = None
    note: str = ""  # le texte de l'IA avant sa balise <reponse>


def _answer_items(text: str) -> tuple[list[Any] | None, str | None]:
    """La liste « offers » de la dernière balise <reponse>, ou le motif qui l'empêche."""
    matches = _ANSWER.findall(text)
    if not matches:
        return None, "pas de balise <reponse> dans la réponse de l'IA"
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return None, "le contenu de <reponse> n'est pas du JSON lisible"
    items = data.get("offers") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return None, "pas de liste « offers » dans <reponse>"
    return items, None


def _loose(url: str) -> str:
    """Une adresse sans « www. » ni barre finale : deuxième chance de la retrouver."""
    parts = urlsplit(url.strip())
    host = parts.netloc.lower().removeprefix("www.")
    return f"{host}{parts.path.rstrip('/')}?{parts.query}"


def select_offers(raw: RawResult, today: date) -> Selection:
    """Les offres de la dernière balise <reponse> dont le lien figure parmi les résultats du
    moteur. Titre, entreprise et lieu viennent du titre du résultat ; une offre datée de plus
    de 14 jours est écartée. Rien si la balise manque ou si le moteur n'a rien rendu. Chaque
    résultat reçoit un verdict, pour que l'essai montre pourquoi il est écarté."""
    selection = Selection(results=len(raw.web_results))
    dates = {result.url: page_date(result.page_age, today) for result in raw.web_results}
    selection.dated = sum(1 for value in dates.values() if value is not None)
    reasons: dict[str, str] = {}  # adresse du moteur -> motif
    unknown: list[Verdict] = []
    items, selection.problem = _answer_items(raw.text)
    selection.note = _squash(raw.text.split("<reponse>")[0])
    if selection.problem and raw.stop_reason == "max_tokens":
        selection.problem += " (réponse coupée : limite de jetons atteinte)"
    known: dict[str, WebResult] = {}
    loose: dict[str, list[WebResult]] = {}
    for result in raw.web_results:
        known.setdefault(_same(result.url), result)
        loose.setdefault(_loose(result.url), []).append(result)
    offers: dict[str, RawOffer] = {}
    for item in items or []:
        if not isinstance(item, dict) or not isinstance(item.get("url"), str):
            continue
        hit = known.get(_same(item["url"]))
        if hit is None and len(near := loose.get(_loose(item["url"]), [])) == 1:
            hit = near[0]
        if hit is None:
            said = item.get("title")
            title = said if isinstance(said, str) else ""
            unknown.append(Verdict(item["url"].strip(), title, None, UNKNOWN_LINK))
            continue
        if hit.url in reasons:
            continue  # même résultat proposé deux fois : le premier verdict compte
        parts = urlsplit(hit.url)
        if parts.scheme != "https" or not parts.netloc or parts.path in ("", "/"):
            reasons[hit.url] = BAD_LINK
            continue
        shown = _squash(hit.title)
        if not shown:
            reasons[hit.url] = NO_TITLE
            continue
        # L'intitulé : le morceau du titre du moteur que l'IA désigne, sinon ce titre entier.
        title = (verbatim(item.get("title"), shown) or shown)[:300]
        if _CODE.match(title):
            reasons[hit.url] = CODE_TITLE
            continue
        selection.proposed += 1
        when = dates[hit.url]
        if when is not None and today - when > MAX_AGE:
            selection.too_old += 1
            reasons[hit.url] = TOO_OLD
            continue
        if len(offers) >= MAX_OFFERS:
            reasons[hit.url] = OVER_LIMIT
            continue
        selection.undated_kept += when is None
        reasons[hit.url] = KEPT
        offers[hit.url] = RawOffer(
            title=title,
            url=hit.url,
            company=verbatim(item.get("company"), shown),
            location=verbatim(item.get("location"), shown),
        )
    selection.offers = list(offers.values())
    selection.verdicts = [
        Verdict(r.url, _squash(r.title), r.page_age, reasons.get(r.url, NOT_PROPOSED))
        for r in raw.web_results
    ] + unknown
    return selection


def parse_answer(raw: RawResult, today: date | None = None) -> list[RawOffer]:
    return select_offers(raw, today or date.today()).offers
