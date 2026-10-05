"""Lecture d'un e-mail d'alerte par l'IA, pour les sites sans analyseur (docs/11 §2).

L'IA ne reçoit que le texte de l'alerte, nettoyé des adresses e-mail, des numéros de téléphone
et du nom de Kevin ; elle désigne chaque offre par le numéro d'un lien de l'e-mail : elle ne
peut donc pas inventer d'adresse.
"""

import html as html_lib
import json
import re
from dataclasses import dataclass, field
from importlib import resources
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError

from jobbot.llm.proposals import scrub
from jobbot.llm.scoring import InvalidScore
from jobbot.mail.message import ParsedEmail
from jobbot.sources.base import ParsedAlert, RawOffer

PROMPT_VERSION = "alert-v2"
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/alert-v2.md").read_text("utf-8")
# Extraction simple : un petit modèle suffit (environ 0,01 $ par e-mail).
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 4_000
MAX_TEXT = 20_000
MAX_LINKS = 150

_URL = re.compile(r"https?://[^\s<>\"')\]]+")
_LINKEDIN_JOB = re.compile(r"linkedin\.com/(?:comm/)?jobs/view/(\d+)", re.IGNORECASE)
_UUID = re.compile(r"/detail/([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", re.IGNORECASE)


class ExtractedOffer(BaseModel):
    title: str = Field(min_length=1)
    company: str | None = None
    location: str | None = None
    rate: str | None = None
    link: int
    logo: int | None = None


class AlertOutput(BaseModel):
    offers: list[ExtractedOffer] = Field(max_length=60)


_NULLABLE = {"anyOf": [{"type": "string"}, {"type": "null"}]}
OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "offers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "company": _NULLABLE,
                    "location": _NULLABLE,
                    "rate": _NULLABLE,
                    "link": {"type": "integer"},
                    "logo": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                },
                "required": ["title", "company", "location", "rate", "link", "logo"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["offers"],
    "additionalProperties": False,
}


MAX_IMAGES = 80


@dataclass(frozen=True)
class AlertInput:
    text: str
    links: list[str]
    # (adresse, texte alternatif) des images https de l'e-mail.
    images: list[tuple[str, str]] = field(default_factory=list)


def canonical(url: str) -> tuple[str, str | None]:
    """Lien neutre (sans paramètres de suivi, qui peuvent identifier Kevin) et identifiant."""
    url = html_lib.unescape(url).strip()
    if match := _LINKEDIN_JOB.search(url):
        job_id = match.group(1)
        return f"https://www.linkedin.com/jobs/view/{job_id}/", job_id
    parts = urlsplit(url)
    clean = urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, "", ""))
    match = _UUID.search(parts.path)
    return clean, match.group(1).lower() if match else None


def prepare(email: ParsedEmail, hide: list[str]) -> AlertInput:
    """Texte et liens de l'e-mail, sans coordonnées ni noms à cacher."""
    links: dict[str, None] = {}
    images: dict[str, str] = {}
    html_text = ""
    if email.html:
        soup = BeautifulSoup(email.html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            if href.startswith("http"):
                links[href] = None
        for img in soup.find_all("img", src=True):
            src = str(img["src"]).strip()
            # Les images minuscules (pixels de suivi) n'ont pas de place ici.
            if src.startswith("https://") and str(img.get("width", "")) not in ("1", "0"):
                images.setdefault(src, " ".join(str(img.get("alt", "")).split())[:80])
        html_text = soup.get_text(" ")
    text = html_lib.unescape(email.text or html_text)
    for url in _URL.findall(text):
        links[url] = None
    # Les liens sont donnés à part, numérotés : on les retire du texte.
    text = _URL.sub(" ", text)
    for name in hide:
        if name.strip():
            text = re.sub(re.escape(name.strip()), "[nom retiré]", text, flags=re.IGNORECASE)
    text = scrub(" ".join(text.split()))[:MAX_TEXT]
    return AlertInput(
        text=text, links=list(links)[:MAX_LINKS], images=list(images.items())[:MAX_IMAGES]
    )


def request_params(alert: AlertInput, subject: str | None) -> dict[str, Any]:
    numbered = "\n".join(f"[{i}] {url}" for i, url in enumerate(alert.links, 1))
    pictures = "\n".join(
        f"[{i}] {url} ({alt or 'sans texte'})" for i, (url, alt) in enumerate(alert.images, 1)
    )
    body = alert.text.replace("</email>", "</ email>")
    subject_line = scrub(subject or "")
    content = (
        f"<email>\nobjet : {subject_line}\n\n{body}\n</email>\n\n<liens>\n{numbered}\n</liens>"
        f"\n\n<images>\n{pictures}\n</images>"
    )
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": content}],
        "output_config": {"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
    }


def parse_output(text: str, alert: AlertInput, label: str | None) -> ParsedAlert:
    try:
        output = AlertOutput.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidScore(f"réponse non conforme : {type(exc).__name__}") from exc
    offers: list[RawOffer] = []
    seen: set[str] = set()
    for item in output.offers:
        if not 1 <= item.link <= len(alert.links):
            continue  # numéro de lien inexistant : l'offre est écartée
        url, external_id = canonical(alert.links[item.link - 1])
        if url in seen:
            continue
        seen.add(url)
        location = " ".join(x for x in (item.location, item.rate) if x) or None
        logo = (
            alert.images[item.logo - 1][0]
            if item.logo and 1 <= item.logo <= len(alert.images)
            else None
        )
        offers.append(
            RawOffer(
                title=item.title.strip()[:300],
                company=(item.company or "").strip()[:300] or None,
                location=location[:300] if location else None,
                url=url,
                external_id=external_id,
                logo_url=logo,
            )
        )
    return ParsedAlert(alert_label=label, offers=offers)
