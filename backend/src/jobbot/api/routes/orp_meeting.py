"""Le rendez-vous ORP (docs/83) : la date du prochain, la feuille préparée, ses questions."""

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from jobbot.db.models import OrpMeeting
from jobbot.orp import meeting as service
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


class MeetingOut(BaseModel):
    id: int
    starts_at: datetime
    place: str | None
    advisor: str | None


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


class PreparationOut(BaseModel):
    summaries: list[str]
    works: str | None
    blockers: list[str]
    missing: list[MissingOut]
    offers: int
    questions: list[QuestionIO]
    obligations: list[ObligationOut]


class MeetingPage(BaseModel):
    meeting: MeetingOut | None
    preparation: PreparationOut


def _meeting(found: OrpMeeting | None) -> MeetingOut | None:
    if found is None:
        return None
    return MeetingOut(
        id=found.id, starts_at=found.starts_at, place=found.place, advisor=found.advisor
    )


async def _page(runtime: Runtime) -> MeetingPage:
    async with runtime.sessionmaker() as session:
        prep = await service.prepare(session)
        found = await service.next_meeting(session, datetime.now(UTC))
    return MeetingPage(
        meeting=_meeting(found),
        preparation=PreparationOut(
            summaries=prep.summaries,
            works=prep.works,
            blockers=prep.blockers,
            missing=[MissingOut(**m.__dict__) for m in prep.missing],
            offers=prep.offers,
            questions=[QuestionIO(**q.__dict__) for q in prep.questions],
            obligations=[ObligationOut(**o.__dict__) for o in prep.obligations],
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
