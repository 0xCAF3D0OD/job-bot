"""« Cette note ne me correspond pas » (docs/114) : proposer, puis appliquer une correction."""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from jobbot import plans
from jobbot.db.models import ChunkKind, Evaluation, Offer, ProfileChunk, ScoreCorrection
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


class RetryScoreOut(BaseModel):
    score: int | None


@router.post(
    "/offers/{offer_id}/retry-score",
    operation_id="retryScore",
    responses={
        404: {"description": "Offre inconnue"},
        409: {"description": "La note n'est pas en échec : rien à refaire"},
    },
)
async def retry_score(request: Request, offer_id: int) -> RetryScoreOut:
    """« Réessayer » d'une note impossible après trois échecs de l'IA (A2, décision de Kevin
    du 16.11) : un seul essai, tout de suite ; s'il échoue, la tâche des 10 minutes reprend
    jusqu'au 3e. Refusé hors de cet état, pour ne pas relancer l'IA sur une offre notée."""
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        final = await session.execute(
            select(Evaluation.score_final).where(Evaluation.offer_id == offer_id)
        )
        row = final.first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "offre inconnue")
    if row[0] not in (scoring_service.FINAL_EMPTY, scoring_service.FINAL_ERROR):
        raise HTTPException(status.HTTP_409_CONFLICT, "la note n'est pas en échec")
    return RetryScoreOut(score=await scoring_service.score_offer(runtime, offer_id))


class ScoreNowOut(BaseModel):
    # La note, ou None si elle n'a pas pu être calculée ; `limit` : la phrase de la formule
    # épuisée (aucun appel à l'IA dans ce cas).
    score: int | None = None
    limit: str | None = None


@router.post(
    "/offers/{offer_id}/score-now",
    operation_id="scoreOfferNow",
    responses={
        404: {"description": "Offre inconnue"},
        409: {"description": "L'offre est déjà notée"},
    },
)
async def score_now(request: Request, offer_id: int) -> ScoreNowOut:
    """« Noter maintenant » d'une offre « Pas encore notée » (Kevin, 17.11, Q2 ; planche
    OffreNonNotee du 18.11) : la note tout de suite, environ 10 secondes. Elle compte dans la
    formule ; épuisée, rien ne part à l'IA. Refusé sur une offre déjà notée."""
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        # L'id vient du client : relu sous la RLS du compte (C-5).
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre inconnue")
        score = await session.scalar(
            select(Evaluation.score).where(Evaluation.offer_id == offer_id)
        )
        if score is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "offre déjà notée")
        if offer_id not in await plans.scored_this_month(session):
            try:
                await plans.check(session, plans.SCORE)
            except plans.LimitReached as exc:
                return ScoreNowOut(limit=str(exc))
    return ScoreNowOut(score=await scoring_service.score_offer(runtime, offer_id))
