"""Formations (docs/16 §5) : catalogue vérifié du dépôt et suggestions de l'IA sur demande.

L'IA (Claude Haiku avec la recherche web) ne reçoit que les mots-clés de « Mon domaine »,
les langues lues et les formations déjà connues : rien sur la personne.
"""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources
from typing import Any
from urllib.parse import urlsplit

import anthropic
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import Training
from jobbot.llm.client import Refused
from jobbot.log import get_logger
from jobbot.news import domain
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, budget_state, record_call

log = get_logger(__name__)

KINDS = ("certification", "cours", "parcours", "atelier")
FORMATS = ("self_paced", "live", "in_person", "exam", "exam_online")
LEVELS = ("beginner", "intermediate", "advanced")
PRICES = ("free", "paid")

PROMPT_VERSION = "trainings-v1"
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/trainings-v1.md").read_text("utf-8")
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 6_000
MAX_SEARCHES = 3
MAX_SUGGESTIONS = 10
# Estimation prudente (3 recherches web et les pages lues), pour le plafond mensuel.
ESTIMATE_USD = Decimal("0.06")
_ANSWER = re.compile(r"<reponse>\s*(\{.*\})\s*</reponse>", re.S)


class SuggestUnavailable(Exception):
    """IA non configurée, plafond atteint ou compte API indisponible."""


@dataclass(frozen=True)
class Suggestion:
    title: str
    provider: str
    kind: str
    format: str
    language: str
    price: str
    level: str | None
    duration: str | None
    url: str
    tags: list[str]
    description: str | None


def catalog() -> list[dict[str, Any]]:
    data = json.loads(
        resources.files("jobbot.trainings").joinpath("catalog.json").read_text("utf-8")
    )
    entries: list[dict[str, Any]] = data["trainings"]
    return entries


async def sync_catalog(session: AsyncSession) -> None:
    """Le catalogue du dépôt fait foi : ses fiches sont créées ou mises à jour (par adresse)."""
    for entry in catalog():
        values = {**entry, "origin": "catalog", "verified": True}
        fields = {k: v for k, v in values.items() if k != "url"}
        await session.execute(
            insert(Training)
            .values(**values)
            .on_conflict_do_update(index_elements=["url"], set_=fields)
        )


def _text(value: object, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned[:limit] or None


def parse_answer(text: str) -> list[Suggestion]:
    """Formations valides de la dernière balise <reponse> ; les autres sont ignorées."""
    matches = _ANSWER.findall(text)
    if not matches:
        return []
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return []
    items = data.get("formations") if isinstance(data, dict) else None
    found: list[Suggestion] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        url = _text(item.get("url"), 500) or ""
        title = _text(item.get("title"), 150)
        provider = _text(item.get("provider"), 80)
        language = _text(item.get("language"), 2)
        if (
            not url.startswith("https://")
            or not urlsplit(url).hostname
            or not title
            or not provider
            or not language
            or not language.isalpha()
            or item.get("kind") not in KINDS
            or item.get("format") not in FORMATS
            or item.get("price") not in PRICES
        ):
            continue
        tags = item.get("tags")
        found.append(
            Suggestion(
                title=title,
                provider=provider,
                kind=item["kind"],
                format=item["format"],
                language=language.lower(),
                price=item["price"],
                level=item.get("level") if item.get("level") in LEVELS else None,
                duration=_text(item.get("duration"), 40),
                url=url,
                tags=[t for t in (_text(t, 30) for t in tags) if t][:5]
                if isinstance(tags, list)
                else [],
                description=_text(item.get("description"), 400),
            )
        )
    return found[:MAX_SUGGESTIONS]


def request_params(keywords: list[str], languages: list[str], known: list[str]) -> dict[str, Any]:
    def clean(value: str) -> str:
        return " ".join(value.replace("<", " ").replace(">", " ").split())

    content = (
        f"<domaine>{clean(', '.join(keywords))[:400]}</domaine>\n"
        f"<langues>{clean(', '.join(languages))[:40]}</langues>\n"
        f"<deja_connues>{clean(' ; '.join(known))[:3000]}</deja_connues>"
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


async def suggest(runtime: Runtime) -> int:
    """Demande des formations à l'IA ; renvoie le nombre de nouvelles fiches « à vérifier »."""
    settings = runtime.settings
    if not settings.llm_configured:
        raise SuggestUnavailable("IA non configurée (JOBBOT_ANTHROPIC_API_KEY)")
    async with runtime.sessionmaker() as session:
        keywords = await domain.keywords(session)
        if not keywords:
            raise SuggestUnavailable("indique d'abord ton domaine dans Réglages → Actualités")
        languages = await domain.languages(session)
        known = [f"{t.title} ({t.provider})" for t in await session.scalars(select(Training))]
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if spend + ESTIMATE_USD * rate > budget:
        raise SuggestUnavailable("plafond mensuel de l'IA atteint")
    client = scoring_service.make_client(settings)
    try:
        raw = await client.score(request_params(keywords, languages, known))
    except Refused:
        return 0
    except anthropic.APIStatusError as exc:
        if problem := account_problem(exc):
            raise SuggestUnavailable(problem) from None
        raise
    found = parse_answer(raw.text)
    added = 0
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=None, rate=rate, purpose="training")
        for item in found:
            inserted = await session.scalar(
                insert(Training)
                .values(**item.__dict__, origin="ai", verified=False)
                .on_conflict_do_nothing(index_elements=["url"])
                .returning(Training.id)
            )
            added += inserted is not None
    log.info("trainings_suggested", proposed=len(found), added=added)
    return added
