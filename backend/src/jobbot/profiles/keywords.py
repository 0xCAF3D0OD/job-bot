"""Mots-clés « Mon domaine » proposés par l'IA à partir d'un métier (docs/17 §2).

Claude Haiku ne reçoit que le métier saisi ; environ 0,001 $ par proposition.
"""

import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources
from typing import Any

import anthropic

from jobbot.llm.client import Refused
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import account_problem, budget_state, record_call

PROMPT_VERSION = "keywords-v1"
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/keywords-v1.md").read_text("utf-8")
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 400
MAX_KEYWORDS = 10
ESTIMATE_USD = Decimal("0.005")
_ANSWER = re.compile(r"<reponse>\s*(\{.*\})\s*</reponse>", re.S)


class KeywordsUnavailable(Exception):
    """IA non configurée, plafond atteint ou compte API indisponible."""


def request_params(occupation: str) -> dict[str, Any]:
    cleaned = " ".join(occupation.replace("<", " ").replace(">", " ").split())[:120]
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [{"role": "user", "content": f"<metier>{cleaned}</metier>"}],
    }


def parse_answer(text: str) -> list[str]:
    matches = _ANSWER.findall(text)
    if not matches:
        return []
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return []
    values = data.get("keywords") if isinstance(data, dict) else None
    found: dict[str, str] = {}
    for value in values if isinstance(values, list) else []:
        if isinstance(value, str) and (cleaned := " ".join(value.split())[:40]):
            found.setdefault(cleaned.casefold(), cleaned)
    return list(found.values())[:MAX_KEYWORDS]


async def propose(runtime: Runtime, occupation: str) -> list[str]:
    settings = runtime.settings
    if not settings.llm_configured:
        raise KeywordsUnavailable("IA non configurée (JOBBOT_ANTHROPIC_API_KEY)")
    async with runtime.sessionmaker() as session:
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
    if spend + ESTIMATE_USD * rate > budget:
        raise KeywordsUnavailable("plafond mensuel de l'IA atteint")
    client = scoring_service.make_client(settings)
    try:
        raw = await client.score(request_params(occupation))
    except Refused:
        return []
    except anthropic.APIStatusError as exc:
        if problem := account_problem(exc):
            raise KeywordsUnavailable(problem) from None
        raise
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=None, rate=rate, purpose="keywords")
    return parse_answer(raw.text)
