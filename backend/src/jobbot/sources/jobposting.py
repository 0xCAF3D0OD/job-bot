"""Le balisage `JobPosting` (schema.org) des pages d'offres, celui que lit Google Jobs.

Utilisé pour une offre ajoutée par son lien (docs/111) et pour la recherche publique de
jobup (docs/104, 0.80.0).
"""

import html
import json
import re
from typing import Any

from bs4 import BeautifulSoup

LD_JSON = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)


def types(item: dict[str, Any]) -> list[str]:
    value = item.get("@type")
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


def job_posting(page: str) -> dict[str, Any] | None:
    """Le premier `JobPosting` des blocs JSON-LD, y compris dans un `@graph` ou une liste."""
    for match in LD_JSON.finditer(page):
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
                if "JobPosting" in types(item):
                    return item
                if isinstance(item.get("@graph"), list):
                    stack.extend(item["@graph"])
    return None


def text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    soup = BeautifulSoup(html.unescape(value), "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    lines = [" ".join(line.split()) for line in soup.get_text("\n").splitlines()]
    return "\n".join(line for line in lines if line) or None


def location(posting: dict[str, Any]) -> str | None:
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
