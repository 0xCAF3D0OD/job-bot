"""Retours d'entretien (docs/23) : un par entretien, rattaché à la candidature."""

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select

from jobbot.db.models import Application, Interview
from jobbot.interviews import service
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["interviews"])

Short = Annotated[str, Field(max_length=300)]
Long = Annotated[str, Field(max_length=2000)]
Kind = Literal["rh", "manager", "technique", "test", "final", "autre"]
Format = Literal["sur_place", "visio", "telephone"]
Duration = Literal["moins_30", "30_60", "plus_60"]
Interviewer = Literal["rh", "manager", "equipe", "direction"]
Score = Annotated[int, Field(ge=1, le=5)]
NextStep = Literal["rien", "entretien", "reponse", "test"]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class InterviewQuestion(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=300)]
    difficult: bool = False


class InterviewIn(BaseModel):
    """Toutes les réponses sont facultatives, sauf le ressenti global (docs/23 §2)."""

    kind: Kind | None = None
    held_at: date | None = None
    format: Format | None = None
    duration: Duration | None = None
    interviewers: list[Interviewer] = Field(default_factory=list, max_length=4)
    people_count: Annotated[int, Field(ge=1, le=30)] | None = None
    rating: Score
    stress: Score | None = None
    interest: Literal["more", "same", "less"] | None = None
    outlook: Literal["positive", "unsure", "negative"] | None = None
    questions: list[InterviewQuestion] = Field(default_factory=list, max_length=40)
    salary_asked: bool | None = None
    salary_answer: Short | None = None
    went_well: Long | None = None
    went_badly: Long | None = None
    to_prepare: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(
        default_factory=list, max_length=20
    )
    my_questions: Long | None = None
    missed_questions: Long | None = None
    learned: Long | None = None
    warnings: Long | None = None
    next_step: NextStep | None = None
    next_step_at: date | None = None
    thanks: Literal["sent", "no", "todo"] | None = None
    employer_feedback: Long | None = None

    @field_validator(
        "salary_answer",
        "went_well",
        "went_badly",
        "my_questions",
        "missed_questions",
        "learned",
        "warnings",
        "employer_feedback",
    )
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return (value or "").strip() or None

    @field_validator("to_prepare")
    @classmethod
    def _items(cls, values: list[str]) -> list[str]:
        return [v.strip() for v in values if v.strip()]


class InterviewOut(InterviewIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime


def _values(body: InterviewIn) -> dict[str, object]:
    values = body.model_dump()
    values["questions"] = [q.model_dump() for q in body.questions]
    return values


@router.get("/applications/{application_id}/interviews", operation_id="listInterviews")
async def list_interviews(request: Request, application_id: int) -> list[InterviewOut]:
    async with _runtime(request).sessionmaker() as session:
        rows = await session.scalars(
            select(Interview)
            .where(Interview.application_id == application_id)
            .order_by(Interview.held_at.nulls_last(), Interview.id)
        )
        return [InterviewOut.model_validate(r) for r in rows]


@router.post(
    "/applications/{application_id}/interviews",
    operation_id="addInterview",
    status_code=status.HTTP_201_CREATED,
)
async def add_interview(request: Request, application_id: int, body: InterviewIn) -> InterviewOut:
    async with _runtime(request).sessionmaker.begin() as session:
        if await session.get(Application, application_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "candidature introuvable")
        interview = Interview(application_id=application_id, **_values(body))
        session.add(interview)
        await session.flush()
        await session.refresh(interview)
        return InterviewOut.model_validate(interview)


@router.put("/interviews/{interview_id}", operation_id="updateInterview")
async def update_interview(request: Request, interview_id: int, body: InterviewIn) -> InterviewOut:
    async with _runtime(request).sessionmaker.begin() as session:
        interview = await session.get(Interview, interview_id)
        if interview is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "retour introuvable")
        for key, value in _values(body).items():
            setattr(interview, key, value)
        await session.flush()
        await session.refresh(interview)
        return InterviewOut.model_validate(interview)


@router.delete(
    "/interviews/{interview_id}",
    operation_id="deleteInterview",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_interview(request: Request, interview_id: int) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        interview = await session.get(Interview, interview_id)
        if interview is not None:
            await session.delete(interview)


# --- Enseignements et conseils (docs/23 §3) ----------------------------------------------


class QuestionStatOut(BaseModel):
    text: str
    count: int
    difficult: int


class NoteOut(BaseModel):
    company: str
    held_at: date | None
    text: str


class PrepareItem(BaseModel):
    text: str
    done: bool


class CoachingOut(BaseModel):
    created_at: datetime
    application_id: int | None
    pistes: list[str]
    answers: list[dict[str, str]]
    questions_to_ask: list[str]


class InsightsOut(BaseModel):
    count: int
    average_rating: float | None
    # Les questions difficiles d'abord, puis les plus fréquentes.
    questions: list[QuestionStatOut]
    went_well: list[NoteOut]
    went_badly: list[NoteOut]
    to_prepare: list[PrepareItem]
    missed_questions: list[NoteOut]
    employer_feedback: list[NoteOut]
    coaching: CoachingOut | None
    can_coach: bool


class PreparedIn(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=200)]
    done: bool


class CoachIn(BaseModel):
    # Prochain entretien à préparer, facultatif.
    application_id: int | None = None


async def _insights(runtime: Runtime) -> InsightsOut:
    async with runtime.sessionmaker() as session:
        found = await service.insights(session)
        coaching = await service.last_coaching(session)
    return InsightsOut(
        count=found.count,
        average_rating=found.average_rating,
        questions=[QuestionStatOut(**q.__dict__) for q in found.questions],
        went_well=[NoteOut(**n.__dict__) for n in found.went_well],
        went_badly=[NoteOut(**n.__dict__) for n in found.went_badly],
        to_prepare=[PrepareItem(text=t, done=d) for t, d in found.to_prepare],
        missed_questions=[NoteOut(**n.__dict__) for n in found.missed_questions],
        employer_feedback=[NoteOut(**n.__dict__) for n in found.employer_feedback],
        coaching=CoachingOut(**coaching.__dict__) if coaching else None,
        can_coach=runtime.settings.llm_configured,
    )


@router.get("/interviews/insights", operation_id="getInterviewInsights")
async def get_insights(request: Request) -> InsightsOut:
    return await _insights(_runtime(request))


@router.put("/interviews/insights/prepared", operation_id="setInterviewPrepared")
async def set_prepared(request: Request, body: PreparedIn) -> InsightsOut:
    """Coche (ou décoche) un point « à préparer »."""
    async with _runtime(request).sessionmaker.begin() as session:
        await service.set_prepared(session, body.text, body.done)
    return await _insights(_runtime(request))


@router.post(
    "/interviews/coach",
    operation_id="coachInterviews",
    responses={409: {"description": "IA indisponible, plafond atteint ou aucun retour"}},
)
async def coach_interviews(request: Request, body: CoachIn) -> InsightsOut:
    """Pistes de l'IA (environ 0,03 $), à partir des retours et des blocs de profil seulement."""
    try:
        await service.coach(_runtime(request), body.application_id)
    except service.CoachUnavailable as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    return await _insights(_runtime(request))
