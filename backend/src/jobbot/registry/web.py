"""Adresse d'une entreprise cherchée sur Internet par l'IA (docs/12, complément 0.7.2).

Dernier recours après le registre IDE. L'IA ne reçoit que le nom de l'entreprise et la ville
de l'offre ; elle rend une adresse suisse avec la page source, ou rien.
"""

import json
import re
from dataclasses import dataclass
from importlib import resources
from typing import Any

PROMPT_VERSION = "address-web-v1"
INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath("prompts/address-web-v1.md").read_text("utf-8")
)
MAX_TOKENS = 4_000
MAX_SEARCHES = 2
# Recherche simple : un petit modèle suffit et coûte environ 5 fois moins que la notation
# (les pages lues pèsent quelque 15 000 jetons d'entrée). Recherche web de base, sans effort.
MODEL = "claude-haiku-4-5"
_ANSWER = re.compile(r"<reponse>\s*(\{.*?\})\s*</reponse>", re.S)
_POSTCODE = re.compile(r"^\d{4}$")


@dataclass(frozen=True)
class WebAddress:
    street: str
    postcode: str
    town: str
    source_url: str

    @property
    def address(self) -> str:
        return f"{self.street}\n{self.postcode} {self.town}"


def request_params(company: str, town: str | None, model: str = MODEL) -> dict[str, Any]:
    def clean(value: str) -> str:
        return " ".join(value.replace("<", " ").replace(">", " ").split())[:150]

    content = (
        f"<entreprise>{clean(company)}</entreprise>\n<ville>{clean(town or 'inconnue')}</ville>"
    )
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


def parse_answer(text: str) -> WebAddress | None:
    """La dernière balise <reponse> ; None si absente, invalide ou sans adresse sûre."""
    matches = _ANSWER.findall(text)
    if not matches:
        return None
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("found") is not True:
        return None

    def field(key: str) -> str:
        value = data.get(key)
        return " ".join(str(value).split()) if isinstance(value, (str, int)) else ""

    street, postcode, town, url = (field(k) for k in ("street", "postcode", "town", "source_url"))
    if not street or not town or not _POSTCODE.match(postcode) or not url.startswith("https://"):
        return None
    return WebAddress(street[:150], postcode, town[:80], url[:500])
