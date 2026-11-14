"""Les premières offres par la recherche web de l'IA (docs/104, « Premières offres par le web »).

jobA1 n'ouvre aucune page d'annonce et ne lit aucun site d'emploi : il demande une recherche
web à l'IA (l'outil déjà utilisé pour les adresses et les formations) et n'en garde que
l'intitulé, l'entreprise et le lieu quand le résultat les montre, et le lien. Chaque lien est
vérifié contre ceux que le moteur a réellement rendus : un lien que l'IA aurait inventé est
écarté. Ces offres ne sont ni lues ni notées (pas de texte d'annonce).
"""

import json
import re
from decimal import Decimal
from importlib import resources
from typing import Any
from urllib.parse import urlsplit

from jobbot.db.models import WEB_LINK_SOURCE
from jobbot.llm.client import RawResult
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
_ANSWER = re.compile(r"<reponse>\s*(\{.*\})\s*</reponse>", re.S)
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


def parse_answer(raw: RawResult) -> list[RawOffer]:
    """Les offres de la dernière balise <reponse>, dont le lien figure parmi les résultats du
    moteur. Rien si la balise manque, est invalide, ou si le moteur n'a rendu aucun lien."""
    matches = _ANSWER.findall(raw.text)
    if not matches or not raw.web_urls:
        return []
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return []
    items = data.get("offers") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    known = {_same(url) for url in raw.web_urls}
    offers: dict[str, RawOffer] = {}

    def field(item: dict[str, Any], key: str, limit: int) -> str | None:
        value = item.get(key)
        cleaned = " ".join(value.split())[:limit] if isinstance(value, str) else ""
        return cleaned or None

    for item in items:
        if not isinstance(item, dict):
            continue
        title, url = field(item, "title", 300), field(item, "url", 1000)
        if not title or not url or _CODE.match(title):
            continue
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.netloc or parts.path in ("", "/"):
            continue
        if _same(url) not in known:
            continue
        offers.setdefault(
            _same(url),
            RawOffer(
                title=title,
                url=url,
                company=field(item, "company", 300),
                location=field(item, "location", 200),
            ),
        )
    return list(offers.values())[:MAX_OFFERS]
