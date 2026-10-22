"""Comparer deux modèles de notation sur tes offres déjà notées (docs/125 §9) : avant de passer
la note à un modèle moins cher, on vérifie qu'elle reste juste. Rien n'est enregistré dans les
notes ; les appels sont comptés dans le plafond, comme tout appel à l'IA."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from jobbot.db.models import Evaluation, LlmCall, Offer
from jobbot.llm.client import Refused
from jobbot.llm.pricing import cost_usd
from jobbot.llm.scoring import parse_output, request_params
from jobbot.runtime import Runtime
from jobbot.scoring.service import (
    active_profile,
    budget_state,
    make_client,
    offer_data,
    record_call,
)


def word(score: int) -> str:
    """Les mots de la note (docs/121 §C.5)."""
    if score >= 85:
        return "Très proche"
    if score >= 70:
        return "Proche"
    if score >= 50:
        return "À creuser"
    return "Loin"


@dataclass(frozen=True)
class Row:
    title: str
    current: int
    other: int | None
    current_usd: Decimal | None
    other_usd: Decimal | None


async def compare(runtime: Runtime, model: str, limit: int) -> list[Row]:
    settings = runtime.settings
    client = make_client(settings)
    async with runtime.sessionmaker() as session:
        profile = await active_profile(session)
        pairs = list(
            (
                await session.execute(
                    select(Offer, Evaluation.score)
                    .join(Evaluation, Evaluation.offer_id == Offer.id)
                    .where(Evaluation.score.is_not(None))
                    .order_by(Evaluation.scored_at.desc())
                    .limit(limit)
                )
            ).all()
        )
        _, _, rate = await budget_state(session, datetime.now(UTC))
    rows = []
    for offer, score in pairs:
        current = int(score or 0)
        async with runtime.sessionmaker() as session:
            current_usd = await session.scalar(
                select(LlmCall.cost_usd)
                .where(LlmCall.offer_id == offer.id, LlmCall.purpose == "score")
                .order_by(LlmCall.created_at.desc())
                .limit(1)
            )
        params = request_params(model, settings.llm_effort, profile, offer_data(offer))
        try:
            raw = await client.score(params)
        except Refused:
            rows.append(Row(offer.title, current, None, current_usd, None))
            continue
        async with runtime.sessionmaker.begin() as session:
            await record_call(session, raw, offer_id=None, rate=rate, purpose="compare")
        other = parse_output(raw.text, profile).score
        rows.append(Row(offer.title, current, other, current_usd, cost_usd(raw.model, raw.usage)))
    return rows
