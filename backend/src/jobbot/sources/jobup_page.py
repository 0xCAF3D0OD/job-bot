"""Lecture d'une page d'offre publique jobup (docs/05-candidature-externe.md).

Deux sources dans la page :
- le bloc JSON-LD `JobPosting` (format standard schema.org) : texte complet de l'annonce,
  type d'emploi ;
- l'objet `applicationOptions` de l'état de la page : méthode de candidature et lien externe.
"""

import html
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from bs4 import BeautifulSoup

_LD_JSON = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
# Objet plat : {"isApplicationMethodOnline":false,"method":"…","externalUrl":"…"}
_APPLICATION = re.compile(r'"applicationOptions":(\{[^{}]*\})')
_EXTERNAL = "APPLICATION_METHOD.EXTERNAL"


class ApplyKind(StrEnum):
    EXTERNAL = "external"  # candidature chez l'employeur ou son outil de recrutement
    JOBUP = "jobup"  # formulaire de candidature jobup


@dataclass(frozen=True)
class JobupPage:
    apply_kind: ApplyKind
    apply_url: str
    description: str | None
    employment_type: str | None
    # Adresse du lieu de travail (JSON-LD « jobLocation »), sur deux lignes : rue, NPA localité.
    address: str | None = None


class PageNotParsable(ValueError):
    """La page ne contient pas l'annonce (format changé, page d'erreur)."""


def _job_posting(page: str) -> dict[str, Any] | None:
    for match in _LD_JSON.finditer(page):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                return item
    return None


def _html_to_text(value: str) -> str:
    soup = BeautifulSoup(value, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    blocks = [
        " ".join(element.get_text(" ", strip=True).split())
        for element in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "div"])
        if not element.find(["p", "li", "div"])
    ]
    text = "\n".join(b for b in blocks if b)
    return text or " ".join(soup.get_text(" ", strip=True).split())


def parse_jobup_page(page: str, offer_url: str) -> JobupPage:
    posting = _job_posting(page)
    application = _APPLICATION.search(page)
    if posting is None and application is None:
        raise PageNotParsable("ni annonce JobPosting ni options de candidature dans la page")

    kind, url = ApplyKind.JOBUP, offer_url
    if application:
        # L'état de la page est du JavaScript : « undefined » n'est pas du JSON.
        options = json.loads(application.group(1).replace(":undefined", ":null"))
        external = (options.get("externalUrl") or "").strip()
        if options.get("method") == _EXTERNAL and external.startswith(("http://", "https://")):
            kind, url = ApplyKind.EXTERNAL, external

    description = None
    employment_type = None
    if posting:
        raw = posting.get("description")
        if isinstance(raw, str) and raw.strip():
            description = _html_to_text(html.unescape(raw)) or None
        value = posting.get("employmentType")
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        employment_type = str(value).strip() if value else None
    return JobupPage(kind, url, description, employment_type, _address(posting))


def _address(posting: dict[str, Any] | None) -> str | None:
    """« Chemin Malombré 10\n1206 Genève » ; None si la rue ou le NPA manque."""
    if not posting:
        return None
    locations = posting.get("jobLocation")
    location = locations[0] if isinstance(locations, list) and locations else locations
    if not isinstance(location, dict) or not isinstance(location.get("address"), dict):
        return None
    address = location["address"]

    def text(key: str) -> str:
        value = address.get(key)
        return " ".join(str(value).split()) if value else ""

    street = text("streetAddress")
    postcode = text("postalCode")
    town = text("addressLocality") or text("addressRegion")
    if not street or not postcode:
        return None
    return f"{street}\n{postcode} {town}".strip()
