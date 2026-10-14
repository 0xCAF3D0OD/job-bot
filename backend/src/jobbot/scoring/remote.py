"""Relecture du télétravail des offres déjà notées (docs/26 §2), sur clic de Kevin.

Les offres notées avant score-v3 n'ont pas le télétravail relevé ; plutôt que de refaire
leur note (cher), un modèle léger relit seulement ce point, pour les offres à examiner.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources
from typing import Any

import anthropic
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import Evaluation, Offer
from jobbot.filtering.service import run_filter
from jobbot.llm.client import Refused
from jobbot.llm.scoring import RemoteOutput, offer_message, remote_fields
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import TO_SCORE, account_problem, budget_state, offer_data, record_call

log = get_logger(__name__)

PROMPT_VERSION = "remote-v1"
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 200
# Estimation prudente d'une relecture, pour respecter le plafond (environ 0,001 $).
ESTIMATE_USD = Decimal("0.002")
LIMIT = 300
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/remote-v1.md").read_text("utf-8")
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "remote": {"type": "string", "enum": ["onsite", "hybrid", "full", "unknown"]},
        "remote_days": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "remote_region": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "remote_from_switzerland": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
    },
    "required": ["remote", "remote_days", "remote_region", "remote_from_switzerland"],
    "additionalProperties": False,
}


def pending_query() -> Any:
    """Offres à examiner, notées, dont le télétravail n'est pas encore relevé."""
    return (
        select(Offer)
        .join(Evaluation, Evaluation.offer_id == Offer.id)
        .where(
            Offer.status.in_(TO_SCORE),
            Offer.expired_at.is_(None),
            Evaluation.scored_at.is_not(None),
            Evaluation.remote.is_(None),
        )
        .order_by(Offer.first_seen_at.desc(), Offer.id.desc())
    )


async def pending_count(session: AsyncSession) -> int:
    return len(list(await session.scalars(pending_query().limit(LIMIT))))


@dataclass
class RemoteResult:
    read: int = 0
    failed: int = 0
    budget_reached: bool = False


async def run_remote(runtime: Runtime) -> RemoteResult:
    result = RemoteResult()
    async with runtime.sessionmaker() as session:
        offers = list(await session.scalars(pending_query().limit(LIMIT)))
    if not offers or not runtime.settings.llm_configured:
        return result
    client = scoring_service.make_client(runtime.settings)
    for offer in offers:
        async with runtime.sessionmaker() as session:
            spend, budget, rate = await budget_state(session, datetime.now(UTC))
        if spend + ESTIMATE_USD * rate > budget:
            result.budget_reached = True
            break
        params = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "system": [{"type": "text", "text": INSTRUCTIONS}],
            "messages": [{"role": "user", "content": offer_message(offer_data(offer))}],
            "output_config": {"format": {"type": "json_schema", "schema": SCHEMA}},
        }
        try:
            raw = await client.score(params)
        except Refused:
            result.failed += 1
            continue
        except anthropic.APIStatusError as exc:
            if account_problem(exc):
                break
            result.failed += 1
            continue
        try:
            fields = remote_fields(RemoteOutput.model_validate(json.loads(raw.text)))
        except (json.JSONDecodeError, ValidationError):
            fields = None
        async with runtime.sessionmaker.begin() as session:
            await record_call(session, raw, offer_id=offer.id, rate=rate, purpose="remote")
            if fields is None:
                result.failed += 1
                continue
            await session.execute(
                update(Evaluation).where(Evaluation.offer_id == offer.id).values(**fields)
            )
        result.read += 1
    if result.read:
        # « Ouvert depuis la Suisse » : les offres réservées à d'autres pays sont écartées.
        await run_filter(runtime)
    log.info("remote_read", read=result.read, failed=result.failed)
    return result
