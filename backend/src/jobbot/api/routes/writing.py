"""Étapes communes à la rédaction de la lettre et du CV par l'IA (docs/08 §3 et §4).

Vérifications (IA configurée, profil, plafond), appel et ses erreurs, enregistrement d'une
nouvelle version. Les coordonnées de Kevin n'interviennent jamais ici.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import anthropic
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import Draft, Evaluation, Offer, OfferStatus
from jobbot.llm.client import RawResult, Refused
from jobbot.llm.letter import Assessment
from jobbot.llm.scoring import OfferData, ProfileChunkData
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service
from jobbot.scoring.service import (
    account_problem,
    active_profile,
    budget_state,
    offer_data,
    record_call,
)

NOUN = {"letter": "lettre", "cv": "CV"}


@dataclass(frozen=True)
class WritingContext:
    offer: OfferData
    chunks: list[ProfileChunkData]
    assessment: Assessment | None
    # Version à retravailler, quand Kevin donne une consigne.
    previous: dict[str, Any] | None
    rate: Decimal


async def get_draft(session: AsyncSession, draft_id: int, kind: str) -> Draft:
    draft = await session.get(Draft, draft_id)
    if draft is None or draft.kind != kind:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{NOUN[kind]} introuvable")
    return draft


async def prepare(
    runtime: Runtime,
    offer_id: int,
    kind: str,
    *,
    base_draft_id: int | None,
    instruction: str | None,
    estimate_usd: Decimal,
) -> WritingContext:
    if not runtime.settings.llm_configured:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "IA non configurée : renseigner JOBBOT_ANTHROPIC_API_KEY."
        )
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        chunks = await active_profile(session)
        if not chunks:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "aucun bloc de profil actif : rien à rédiger",
            )
        evaluation = await session.scalar(select(Evaluation).where(Evaluation.offer_id == offer_id))
        previous = None
        if base_draft_id is not None:
            base = await get_draft(session, base_draft_id, kind)
            if base.offer_id != offer_id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, f"{NOUN[kind]} introuvable")
            previous = base.content
        elif instruction:
            latest = await session.scalar(
                select(Draft)
                .where(Draft.offer_id == offer_id, Draft.kind == kind)
                .order_by(Draft.version.desc())
                .limit(1)
            )
            previous = latest.content if latest else None
        spend, budget, rate = await budget_state(session, datetime.now(UTC))
        data = offer_data(offer)
    if spend + estimate_usd * rate > budget:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "plafond mensuel de l'IA atteint : le relever dans les Réglages",
        )
    assessment = None
    if evaluation is not None:
        assessment = Assessment(
            strengths=[p["text"] for p in evaluation.strengths or []],
            gaps=[p["text"] for p in evaluation.gaps or []],
        )
    return WritingContext(data, chunks, assessment, previous, rate)


async def call(
    runtime: Runtime, params: dict[str, Any], *, offer_id: int, kind: str, rate: Decimal
) -> RawResult:
    """Appel à l'IA ; le coût est enregistré même si la réponse s'avère inutilisable."""
    client = scoring_service.make_client(runtime.settings)
    try:
        raw = await client.score(params)
    except Refused:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"l'IA a refusé de rédiger ce document ({NOUN[kind]})"
        ) from None
    except (anthropic.RateLimitError, anthropic.APIConnectionError):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "IA momentanément indisponible, réessayer"
        ) from None
    except anthropic.APIStatusError as exc:
        problem = account_problem(exc)
        raise HTTPException(
            status.HTTP_409_CONFLICT if problem else status.HTTP_502_BAD_GATEWAY,
            problem or f"erreur de l'API ({exc.status_code})",
        ) from None
    async with runtime.sessionmaker.begin() as session:
        await record_call(session, raw, offer_id=offer_id, rate=rate, purpose=kind)
    return raw


def unusable() -> HTTPException:
    return HTTPException(status.HTTP_502_BAD_GATEWAY, "réponse de l'IA inutilisable, réessayer")


async def add_version(
    session: AsyncSession,
    offer_id: int,
    kind: str,
    *,
    language: str,
    content: dict[str, Any],
    instruction: str | None,
    model: str,
    prompt_version: str,
) -> Draft:
    """Nouvelle version ; l'offre passe « en préparation » si elle n'est pas déjà envoyée."""
    version = await session.scalar(
        select(func.coalesce(func.max(Draft.version), 0)).where(
            Draft.offer_id == offer_id, Draft.kind == kind
        )
    )
    draft = Draft(
        offer_id=offer_id,
        kind=kind,
        version=(version or 0) + 1,
        language=language,
        content=content,
        instruction=instruction,
        model=model,
        prompt_version=prompt_version,
    )
    session.add(draft)
    offer = await session.get(Offer, offer_id)
    if offer is not None and offer.status != OfferStatus.APPLIED:
        offer.status = OfferStatus.PREPARING
    await session.flush()
    await session.refresh(draft)
    return draft
