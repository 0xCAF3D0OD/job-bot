"""Retours d'entretien (docs/23) : un par entretien, rattaché à la candidature."""

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import Application, Interview, InterviewPractice, Offer
from jobbot.interviews import practice, service
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


@router.post("/interviews/insights/to-prepare", operation_id="addInterviewToPrepare")
async def add_to_prepare(request: Request, body: PreparedIn) -> InsightsOut:
    """Ajoute un point à travailler, tiré du retour d'un entraînement (docs/75 §7)."""
    async with _runtime(request).sessionmaker.begin() as session:
        await service.add_to_prepare(session, body.text.strip())
    return await _insights(_runtime(request))


# --- S'entraîner à l'entretien (docs/75) ---------------------------------------------------

PracticeKind = Literal["rh", "manager", "technique"]
Tone = Literal["bienveillant", "exigeant"]
Language = Literal["fr", "en", "de"]
Level = Literal["solide", "a_preciser", "a_retravailler"]


class PracticeIn(BaseModel):
    application_id: int | None = None
    kind: PracticeKind = "rh"
    tone: Tone = "bienveillant"
    language: Language = "fr"


class PracticeAnswerIn(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=practice.ANSWER_MAX)]


class PracticeTurn(BaseModel):
    role: Literal["recruteur", "candidat"]
    text: str
    question: int
    relance: bool = False
    skipped: bool = False


class PracticeQuestionFeedback(BaseModel):
    question: int
    level: Level
    good: str
    missing: str
    better: str


class PracticeFeedback(BaseModel):
    questions: list[PracticeQuestionFeedback]
    strengths: list[str]
    work_on: list[str]


class PracticeOut(BaseModel):
    id: int
    application_id: int | None
    company: str | None
    job_title: str | None
    kind: PracticeKind
    tone: Tone
    language: Language
    status: Literal["en_cours", "termine"]
    question: int
    questions: int
    # Le recruteur n'a pas encore parlé (erreur de l'IA) : « Réessayer ».
    waiting: bool
    turns: list[PracticeTurn]
    feedback: PracticeFeedback | None
    cost_chf: float
    created_at: datetime


class PracticeDefaults(BaseModel):
    kind: PracticeKind
    language: Language
    can_practice: bool


async def _practice_out(session: AsyncSession, item: InterviewPractice) -> PracticeOut:
    application = (
        await session.get(Application, item.application_id) if item.application_id else None
    )
    turns = list(item.turns or [])
    return PracticeOut(
        id=item.id,
        application_id=item.application_id,
        company=application.company if application else None,
        job_title=application.job_title if application else None,
        kind=item.kind,
        tone=item.tone,
        language=item.language,
        status=item.status,
        question=practice.current_question(turns),
        questions=practice.QUESTIONS,
        waiting=item.status == "en_cours" and (not turns or turns[-1].get("role") != "recruteur"),
        turns=[PracticeTurn(**t) for t in turns],
        feedback=PracticeFeedback(**item.feedback) if item.feedback else None,
        cost_chf=float(item.cost_chf or 0),
        created_at=item.created_at,
    )


async def _one(runtime: Runtime, practice_id: int) -> PracticeOut:
    async with runtime.sessionmaker() as session:
        item = await session.get(InterviewPractice, practice_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Entraînement introuvable")
        return await _practice_out(session, item)


def _unavailable(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    return HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get("/interview-practices/defaults", operation_id="getPracticeDefaults")
async def practice_defaults(
    request: Request, application_id: int | None = None
) -> PracticeDefaults:
    """Le type du dernier entretien noté pour cette candidature, la langue de l'annonce."""
    runtime = _runtime(request)
    kind: PracticeKind = "rh"
    language: Language = "fr"
    async with runtime.sessionmaker() as session:
        if application_id is not None:
            last = await session.scalar(
                select(Interview.kind)
                .where(Interview.application_id == application_id)
                .order_by(Interview.id.desc())
                .limit(1)
            )
            if last == "manager":
                kind = "manager"
            elif last == "technique":
                kind = "technique"
            application = await session.get(Application, application_id)
            if application is not None and application.offer_id:
                offer = await session.get(Offer, application.offer_id)
                if offer is not None:
                    language = practice.guess_language(  # type: ignore[assignment]
                        f"{offer.title} {offer.description or offer.snippet or ''}"
                    )
    return PracticeDefaults(
        kind=kind, language=language, can_practice=runtime.settings.llm_configured
    )


@router.get("/interview-practices", operation_id="listPractices")
async def list_practices(request: Request, application_id: int | None = None) -> list[PracticeOut]:
    async with _runtime(request).sessionmaker() as session:
        query = select(InterviewPractice).order_by(InterviewPractice.created_at.desc())
        if application_id is not None:
            query = query.where(InterviewPractice.application_id == application_id)
        return [await _practice_out(session, item) for item in await session.scalars(query)]


@router.post(
    "/interview-practices",
    operation_id="startPractice",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "IA indisponible ou plafond atteint"}},
)
async def start_practice(request: Request, body: PracticeIn) -> PracticeOut:
    """Démarre un entretien blanc : la première question du recruteur (docs/75)."""
    runtime = _runtime(request)
    try:
        practice_id = await practice.start(
            runtime, body.application_id, body.kind, body.tone, body.language
        )
    except (practice.PracticeUnavailable, LookupError) as exc:
        raise _unavailable(exc) from None
    return await _one(runtime, practice_id)


@router.get("/interview-practices/{practice_id}", operation_id="getPractice")
async def get_practice(request: Request, practice_id: int) -> PracticeOut:
    return await _one(_runtime(request), practice_id)


@router.post(
    "/interview-practices/{practice_id}/answer",
    operation_id="answerPractice",
    responses={409: {"description": "IA indisponible, plafond atteint ou entraînement terminé"}},
)
async def answer_practice(
    request: Request, practice_id: int, body: PracticeAnswerIn
) -> PracticeOut:
    runtime = _runtime(request)
    try:
        await practice.answer(runtime, practice_id, body.text)
    except (practice.PracticeUnavailable, LookupError) as exc:
        raise _unavailable(exc) from None
    return await _one(runtime, practice_id)


@router.post(
    "/interview-practices/{practice_id}/skip",
    operation_id="skipPracticeQuestion",
    responses={409: {"description": "IA indisponible ou entraînement terminé"}},
)
async def skip_practice(request: Request, practice_id: int) -> PracticeOut:
    runtime = _runtime(request)
    try:
        await practice.skip(runtime, practice_id)
    except (practice.PracticeUnavailable, LookupError) as exc:
        raise _unavailable(exc) from None
    return await _one(runtime, practice_id)


@router.post(
    "/interview-practices/{practice_id}/retry",
    operation_id="retryPractice",
    responses={409: {"description": "IA indisponible"}},
)
async def retry_practice(request: Request, practice_id: int) -> PracticeOut:
    runtime = _runtime(request)
    try:
        await practice.retry(runtime, practice_id)
    except (practice.PracticeUnavailable, LookupError) as exc:
        raise _unavailable(exc) from None
    return await _one(runtime, practice_id)


@router.post(
    "/interview-practices/{practice_id}/finish",
    operation_id="finishPractice",
    responses={409: {"description": "IA indisponible ou aucune réponse"}},
)
async def finish_practice(request: Request, practice_id: int) -> PracticeOut:
    """« Terminer et voir le retour », à tout moment après une réponse."""
    runtime = _runtime(request)
    try:
        await practice.finish(runtime, practice_id)
    except (practice.PracticeUnavailable, LookupError) as exc:
        raise _unavailable(exc) from None
    return await _one(runtime, practice_id)


@router.delete(
    "/interview-practices/{practice_id}",
    operation_id="deletePractice",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_practice(request: Request, practice_id: int) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        item = await session.get(InterviewPractice, practice_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Entraînement introuvable")
        await session.delete(item)
