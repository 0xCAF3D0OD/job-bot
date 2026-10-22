"""« Cette note ne me correspond pas » (docs/114) : proposer, puis appliquer une correction."""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from jobbot.db.models import ChunkKind, Evaluation, ProfileChunk, ScoreCorrection
from jobbot.runtime import Runtime
from jobbot.scoring import corrections
from jobbot.scoring import service as scoring_service

router = APIRouter(prefix="/api", tags=["offers"])

Direction = Literal["high", "low"]
Reason = Literal[
    "not_my_trade",
    "not_my_level",
    "sector",
    "place_rate_contract",
    "my_trade",
    "have_experience",
    "sector_ok",
    "other",
]
Note = Annotated[str, Field(max_length=200)]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class CorrectionAsk(BaseModel):
    direction: Direction
    reason: Reason
    note: Note | None = None


class BlockOut(BaseModel):
    kind: Literal["preference", "redhibitoire"]
    title: str
    content: str
    # Rédigé par l'IA, ou par le modèle simple (IA absente ou au plafond).
    by_ai: bool


class CriteriaChangeOut(BaseModel):
    key: str
    label: str
    changes: dict[str, Any]


class ProposalOut(BaseModel):
    block: BlockOut | None = None
    criteria: list[CriteriaChangeOut] = []


class BlockIn(BaseModel):
    kind: Literal["preference", "redhibitoire"]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    content: Annotated[str, Field(min_length=1, max_length=2000)]

    @field_validator("title", "content")
    @classmethod
    def _strip(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("ne doit pas être vide")
        return value.strip()


class CorrectionIn(CorrectionAsk):
    block: BlockIn | None = None
    criteria: dict[str, Any] | None = None


class CorrectionOut(BaseModel):
    direction: Direction
    reason: Reason
    note: str | None
    chunk_id: int | None
    score_before: int | None
    # La note après correction (renotée si un bloc a été ajouté).
    score: int | None


def _refused(exc: corrections.CorrectionRefused) -> HTTPException:
    code = (
        status.HTTP_404_NOT_FOUND
        if "introuvable" in str(exc)
        else status.HTTP_422_UNPROCESSABLE_CONTENT
    )
    return HTTPException(code, str(exc))


@router.get("/offers/{offer_id}/score-correction", operation_id="getScoreCorrection")
async def get_correction(request: Request, offer_id: int) -> CorrectionOut | None:
    async with _runtime(request).sessionmaker() as session:
        found = await session.scalar(
            select(ScoreCorrection).where(ScoreCorrection.offer_id == offer_id)
        )
        if found is None:
            return None
        score = await session.scalar(
            select(Evaluation.score).where(Evaluation.offer_id == offer_id)
        )
    return CorrectionOut(
        direction=found.direction,
        reason=found.reason,
        note=found.note,
        chunk_id=found.chunk_id,
        score_before=found.score_before,
        score=score,
    )


@router.post("/offers/{offer_id}/score-correction/proposal", operation_id="proposeScoreCorrection")
async def propose(request: Request, offer_id: int, body: CorrectionAsk) -> ProposalOut:
    """Ce que la correction donnerait : un bloc de profil à relire, ou des critères."""
    try:
        found = await corrections.propose(
            _runtime(request), offer_id, body.direction, body.reason, body.note
        )
    except corrections.CorrectionRefused as exc:
        raise _refused(exc) from None
    block = (
        BlockOut(
            kind="redhibitoire" if found.block.kind == ChunkKind.REDHIBITOIRE else "preference",
            title=found.block.title,
            content=found.block.content,
            by_ai=found.block.by_ai,
        )
        if found.block
        else None
    )
    return ProposalOut(
        block=block,
        criteria=[CriteriaChangeOut(**c.__dict__) for c in found.criteria],
    )


@router.put("/offers/{offer_id}/score-correction", operation_id="applyScoreCorrection")
async def apply(request: Request, offer_id: int, body: CorrectionIn) -> CorrectionOut:
    """La correction enregistrée : le bloc ajouté au profil (l'offre renotée), ou le critère
    réglé (le filtre repasse)."""
    block = (
        corrections.Block(kind=body.block.kind, title=body.block.title, content=body.block.content)
        if body.block
        else None
    )
    try:
        done = await corrections.apply(
            _runtime(request),
            offer_id,
            body.direction,
            body.reason,
            body.note,
            block,
            body.criteria,
        )
    except corrections.CorrectionRefused as exc:
        raise _refused(exc) from None
    async with _runtime(request).sessionmaker() as session:
        before = await session.scalar(
            select(ScoreCorrection.score_before).where(ScoreCorrection.offer_id == offer_id)
        )
    return CorrectionOut(
        direction=body.direction,
        reason=body.reason,
        note=(body.note or "").strip() or None,
        chunk_id=done.chunk_id,
        score_before=before,
        score=done.score,
    )


# --- « Je l'ai : l'ajouter au profil » (docs/121 §C.3) --------------------------------------


class GapBlockIn(BaseModel):
    """Un manque de la note que la personne comble : une compétence qu'elle a sans l'avoir
    écrite. Le bloc est relu avant l'envoi ; l'offre est renotée aussitôt."""

    title: Annotated[str, Field(min_length=1, max_length=200)]
    content: Annotated[str, Field(min_length=1, max_length=2000)]

    @field_validator("title", "content")
    @classmethod
    def _strip(cls, value: str) -> str:
        return " ".join(value.split())


class GapBlockOut(BaseModel):
    chunk_id: int
    score: int | None


@router.post(
    "/offers/{offer_id}/gap-block",
    operation_id="addGapBlock",
    status_code=status.HTTP_201_CREATED,
    responses={404: {"description": "Offre inconnue"}},
)
async def add_gap_block(request: Request, offer_id: int, body: GapBlockIn) -> GapBlockOut:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        evaluation = await session.scalar(select(Evaluation).where(Evaluation.offer_id == offer_id))
        if evaluation is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre inconnue")
        chunk = ProfileChunk(
            kind=ChunkKind.COMPETENCE, title=body.title, content=body.content, origin="gap"
        )
        session.add(chunk)
        await session.flush()
        chunk_id = chunk.id
    score = await scoring_service.score_offer(runtime, offer_id)
    return GapBlockOut(chunk_id=chunk_id, score=score)
