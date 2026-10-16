"""État de la note IA et renotation sur demande (docs/06 §4 et §5)."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select

from jobbot.db.models import Evaluation, JobRun, JobRunStatus, LlmBatch, Offer
from jobbot.llm.scoring import COMPATIBLE_VERSIONS, profile_hash
from jobbot.runtime import Runtime
from jobbot.scoring import remote
from jobbot.scoring.service import TO_SCORE, active_profile, budget_details
from jobbot.worker.queue import enqueue
from jobbot.worker.tasks.score import REMOTE_JOB, RESCORE_JOB, SCORE_JOB

router = APIRouter(prefix="/api", tags=["scoring"])


class ScoringStatus(BaseModel):
    configured: bool
    model: str
    month_spend_chf: Decimal
    # Le plafond du compte (docs/65 §4) ; atteint aussi quand la plateforme a atteint le sien.
    budget_chf: Decimal
    budget_reached: bool
    platform_budget_reached: bool = False
    active_chunks: int
    scored: int
    unscored: int
    # Notées avec un autre profil que l'actuel : « Renoter » les met à jour.
    stale: int
    failed: int
    pending_batches: int
    # Erreur de la dernière exécution de la notation, si elle a échoué (crédit épuisé…).
    last_error: str | None


class RescoreResponse(BaseModel):
    result: Literal["queued", "already_queued"]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


@router.get("/scoring", operation_id="getScoringStatus")
async def get_scoring_status(request: Request) -> ScoringStatus:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        profile = await active_profile(session)
        current = profile_hash(profile)
        budget = await budget_details(session, datetime.now(UTC))
        base = (
            select(func.count())
            .select_from(Offer)
            .outerjoin(Evaluation, Evaluation.offer_id == Offer.id)
            .where(Offer.status.in_(TO_SCORE), Offer.expired_at.is_(None))
        )
        scored = await session.scalar(base.where(Evaluation.scored_at.is_not(None))) or 0
        unscored = (
            await session.scalar(
                base.where(
                    or_(
                        Evaluation.id.is_(None),
                        and_(Evaluation.scored_at.is_(None), Evaluation.score_error.is_(None)),
                        Evaluation.prompt_version.not_in(COMPATIBLE_VERSIONS),
                    )
                )
            )
            or 0
        )
        stale = (
            await session.scalar(
                base.where(Evaluation.scored_at.is_not(None), Evaluation.profile_hash != current)
            )
            or 0
        )
        failed = (
            await session.scalar(
                base.where(Evaluation.scored_at.is_(None), Evaluation.score_error.is_not(None))
            )
            or 0
        )
        latest = await session.scalar(
            select(JobRun)
            .where(JobRun.job.in_((SCORE_JOB, RESCORE_JOB)), JobRun.status != JobRunStatus.RUNNING)
            .order_by(JobRun.finished_at.desc())
            .limit(1)
        )
        pending = (
            await session.scalar(
                select(func.count()).select_from(LlmBatch).where(LlmBatch.status == "in_progress")
            )
            or 0
        )
    return ScoringStatus(
        configured=runtime.settings.llm_configured,
        model=runtime.settings.llm_model,
        month_spend_chf=budget.spend.quantize(Decimal("0.01")),
        budget_chf=budget.cap,
        budget_reached=budget.spend >= budget.effective,
        platform_budget_reached=budget.platform_reached,
        active_chunks=len(profile),
        scored=scored,
        unscored=unscored,
        stale=stale,
        failed=failed,
        pending_batches=pending,
        last_error=latest.error if latest and latest.status == JobRunStatus.FAILURE else None,
    )


class RemoteStatus(BaseModel):
    """Offres à examiner déjà notées dont le télétravail n'est pas relevé (docs/26 §2)."""

    pending: int
    estimate_usd: Decimal


@router.get("/scoring/remote", operation_id="getRemoteStatus")
async def get_remote_status(request: Request) -> RemoteStatus:
    async with _runtime(request).sessionmaker() as session:
        pending = await remote.pending_count(session)
    return RemoteStatus(
        pending=pending, estimate_usd=(Decimal("0.001") * pending).quantize(Decimal("0.01"))
    )


@router.post(
    "/scoring/remote",
    operation_id="startRemoteRead",
    status_code=status.HTTP_202_ACCEPTED,
    responses={409: {"description": "IA non configurée"}},
)
async def start_remote_read(request: Request) -> RescoreResponse:
    runtime = _runtime(request)
    if not runtime.settings.llm_configured:
        raise HTTPException(status.HTTP_409_CONFLICT, "IA non configurée")
    queued = await enqueue(runtime.settings, REMOTE_JOB)
    return RescoreResponse(result="queued" if queued else "already_queued")


@router.post(
    "/rescore",
    operation_id="startRescore",
    status_code=status.HTTP_202_ACCEPTED,
    responses={409: {"description": "IA non configurée"}},
)
async def start_rescore(request: Request) -> RescoreResponse:
    runtime = _runtime(request)
    if not runtime.settings.llm_configured:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "IA non configurée : renseigner JOBBOT_ANTHROPIC_API_KEY."
        )
    queued = await enqueue(runtime.settings, RESCORE_JOB)
    return RescoreResponse(result="queued" if queued else "already_queued")
