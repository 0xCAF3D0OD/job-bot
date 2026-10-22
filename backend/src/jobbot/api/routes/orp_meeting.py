"""Le rendez-vous ORP (docs/83) : la date du prochain, la feuille préparée, ses questions ;
ensuite ce qui a été convenu, le carnet, et la feuille rédigée par l'IA sur demande."""

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import OrpMeeting
from jobbot.orp import meeting as service
from jobbot.orp import outcome as outcomes
from jobbot.orp import redaction
from jobbot.orp.service import load_target
from jobbot.orp.sheet import sheet_pdf
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/orp-meeting", tags=["orp"])


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class MeetingIn(BaseModel):
    starts_at: datetime
    place: Annotated[str, Field(max_length=200)] | None = None
    advisor: Annotated[str, Field(max_length=120)] | None = None


class MeasureIO(BaseModel):
    text: Annotated[str, Field(max_length=300)]
    training_id: int | None = None


class MeetingOut(BaseModel):
    id: int
    starts_at: datetime
    place: str | None
    advisor: str | None
    # Ce qui a été convenu (0.67.2) : `outcome_at` vide tant que rien n'est noté.
    outcome_at: datetime | None = None
    agreed_target: int | None = None
    measures: list[MeasureIO] = []
    assignments: str | None = None
    note: str | None = None
    # Les questions cochées, gardées dans le carnet.
    asked: list[str] = []
    next_starts_at: datetime | None = None
    sheet_text: str | None = None


class OutcomeIn(BaseModel):
    target: Annotated[int, Field(ge=1, le=100)] | None = None
    measures: Annotated[list[MeasureIO], Field(max_length=20)] = []
    assignments: Annotated[str, Field(max_length=2000)] | None = None
    note: Annotated[str, Field(max_length=4000)] | None = None
    next_starts_at: datetime | None = None


class FollowedTrainingOut(BaseModel):
    id: int
    title: str
    accepted: bool


class QuestionIO(BaseModel):
    key: Annotated[str, Field(max_length=80)]
    text: Annotated[str, Field(max_length=300)]
    checked: bool = False


class QuestionsIn(BaseModel):
    questions: Annotated[list[QuestionIO], Field(max_length=40)]


class MissingOut(BaseModel):
    skill: str
    count: int
    training_id: int | None
    training_title: str | None


class ObligationOut(BaseModel):
    text: str
    due: date | None
    done: bool


class MonthFactsOut(BaseModel):
    month: str
    count: int
    target: int | None
    answered: int
    interviews: int


class PreparationOut(BaseModel):
    summaries: list[str]
    works: str | None
    blockers: list[str]
    missing: list[MissingOut]
    offers: int
    questions: list[QuestionIO]
    obligations: list[ObligationOut]
    has_applications: bool = True
    # Les chiffres des deux mois, en une ligne chacun sur la page (docs/131).
    months: list[MonthFactsOut] = []


class MeetingPage(BaseModel):
    meeting: MeetingOut | None
    preparation: PreparationOut
    # Le carnet : les rendez-vous passés, du plus récent au plus ancien.
    past: list[MeetingOut]
    # Pour noter ce qui a été convenu : l'objectif actuel et les formations suivies.
    target: int | None
    trainings: list[FollowedTrainingOut]


async def _meeting(session: AsyncSession, found: OrpMeeting | None) -> MeetingOut | None:
    if found is None:
        return None
    questions = found.questions if isinstance(found.questions, list) else []
    return MeetingOut(
        id=found.id,
        starts_at=found.starts_at,
        place=found.place,
        advisor=found.advisor,
        outcome_at=found.outcome_at,
        agreed_target=found.agreed_target,
        measures=[MeasureIO(**m) for m in found.measures or [] if isinstance(m, dict)],
        assignments=found.assignments,
        note=found.note,
        asked=[
            str(q.get("text"))
            for q in questions
            if isinstance(q, dict) and q.get("checked") and q.get("text")
        ],
        next_starts_at=await outcomes.following(session, found),
        sheet_text=found.sheet_text,
    )


async def _page(runtime: Runtime) -> MeetingPage:
    now = datetime.now(UTC)
    async with runtime.sessionmaker() as session:
        prep = await service.prepare(session)
        found = await service.next_meeting(session, now)
        meeting = await _meeting(session, found)
        past = [await _meeting(session, m) for m in await outcomes.past(session, now)]
        target = await load_target(session)
        trainings = await outcomes.followed_trainings(session)
    return MeetingPage(
        meeting=meeting,
        past=[m for m in past if m is not None],
        target=target,
        trainings=[FollowedTrainingOut(**t.__dict__) for t in trainings],
        preparation=PreparationOut(
            summaries=prep.summaries,
            works=prep.works,
            blockers=prep.blockers,
            missing=[MissingOut(**m.__dict__) for m in prep.missing],
            offers=prep.offers,
            questions=[QuestionIO(**q.__dict__) for q in prep.questions],
            obligations=[ObligationOut(**o.__dict__) for o in prep.obligations],
            has_applications=prep.has_applications,
            months=[MonthFactsOut(**m.__dict__) for m in prep.months],
        ),
    )


@router.get("", operation_id="getOrpMeeting")
async def get_orp_meeting(request: Request) -> MeetingPage:
    return await _page(_runtime(request))


@router.put("", operation_id="saveOrpMeeting")
async def save_orp_meeting(request: Request, body: MeetingIn) -> MeetingPage:
    """La date du prochain rendez-vous (créé s'il n'y en a pas)."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        found = await service.next_meeting(session, datetime.now(UTC))
        if found is None:
            found = OrpMeeting(questions=[])
            session.add(found)
        found.starts_at = body.starts_at
        found.place = (body.place or "").strip() or None
        found.advisor = (body.advisor or "").strip() or None
    return await _page(runtime)


@router.delete("", operation_id="deleteOrpMeeting")
async def delete_orp_meeting(request: Request) -> MeetingPage:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        found = await service.next_meeting(session, datetime.now(UTC))
        if found is not None:
            await session.delete(found)
    return await _page(runtime)


@router.put(
    "/questions",
    operation_id="saveOrpMeetingQuestions",
    responses={409: {"description": "Pas de rendez-vous prévu"}},
)
async def save_orp_meeting_questions(request: Request, body: QuestionsIn) -> MeetingPage:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        found = await service.next_meeting(session, datetime.now(UTC))
        if found is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "indique d'abord la date du rendez-vous")
        found.questions = [
            q.model_dump()
            for q in body.questions
            if q.text.strip() or not q.key.startswith("custom:")
        ]
    return await _page(runtime)


@router.get(
    "/feuille.pdf",
    operation_id="getOrpMeetingSheet",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def get_orp_meeting_sheet(request: Request, name: str | None = None) -> Response:
    """La feuille sur une page A4 ; ton nom seulement si tu le donnes (`name`)."""
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        prep = await service.prepare(session)
        found = await service.next_meeting(session, datetime.now(UTC))
    pdf = sheet_pdf(
        prep, starts_at=found.starts_at if found else None, name=(name or "").strip()[:120] or None
    )
    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="rendez-vous-orp.pdf"',
            "Cache-Control": "no-store",
        },
    )


@router.put(
    "/{meeting_id}/convenu",
    operation_id="saveOrpMeetingOutcome",
    responses={404: {"description": "Rendez-vous introuvable"}, 409: {"description": "À venir"}},
)
async def save_orp_meeting_outcome(
    request: Request, meeting_id: int, body: OutcomeIn
) -> MeetingPage:
    """Ce qui a été convenu : l'objectif, les formations accordées et le rendez-vous suivant
    sont mis à jour en même temps."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        found = await session.get(OrpMeeting, meeting_id)
        if found is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "rendez-vous introuvable")
        if found.starts_at > datetime.now(UTC):
            raise HTTPException(status.HTTP_409_CONFLICT, "le rendez-vous n'a pas encore eu lieu")
        await outcomes.save(
            session,
            found,
            outcomes.Outcome(
                target=body.target,
                measures=[outcomes.Measure(m.text, m.training_id) for m in body.measures],
                assignments=body.assignments,
                note=body.note,
                next_starts_at=body.next_starts_at,
            ),
        )
    return await _page(runtime)


@router.post(
    "/redaction",
    operation_id="writeOrpMeetingSheet",
    responses={409: {"description": "IA indisponible ou pas de rendez-vous"}},
)
async def write_orp_meeting_sheet(request: Request) -> MeetingPage:
    """La feuille rédigée par l'IA (moins de 0,05 $), gardée avec le rendez-vous."""
    runtime = _runtime(request)
    try:
        await redaction.write(runtime)
    except redaction.RedactionUnavailable as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    return await _page(runtime)
