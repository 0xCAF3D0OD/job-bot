"""Tes dates dans ton agenda (docs/40) : un fichier par entretien, ou un abonnement."""

import re
import unicodedata
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from jobbot.agenda import ics
from jobbot.agenda import service as agenda
from jobbot.db.models import Application, CalendarToken
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["agenda"])
MEDIA = "text/calendar; charset=utf-8"


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


ORIGIN = re.compile(r"^https?://[A-Za-z0-9.-]+(:\d+)?$")


def _base_url(request: Request, origin: str | None = None) -> str:
    """L'adresse de la plateforme : celle que le navigateur a donnée (elle connaît le tunnel
    et le https), sinon celle de la requête."""
    if origin and ORIGIN.match(origin):
        return origin
    return str(request.base_url).rstrip("/")


def _slug(value: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-") or "entretien"


@router.get(
    "/applications/{application_id}/interview.ics",
    operation_id="downloadInterviewEvent",
    response_class=Response,
    responses={200: {"content": {"text/calendar": {}}}},
)
async def interview_file(
    request: Request, application_id: int, origin: Annotated[str | None, Query()] = None
) -> Response:
    async with _runtime(request).sessionmaker() as session:
        application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "candidature introuvable")
    event = agenda.interview_event(application, _base_url(request, origin))
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "pas d'entretien prévu")
    name = f"entretien-{_slug(application.company)}.ics"
    return Response(
        ics.calendar([event], name=f"Entretien \u2013 {application.company}"),
        media_type=MEDIA,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@router.get("/agenda/feed/{token}.ics", include_in_schema=False)
async def feed(request: Request, token: str) -> Response:
    async with _runtime(request).sessionmaker.begin() as session:
        found = await agenda.authenticate(session, token)
        if found is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "abonnement introuvable")
        events = await agenda.events(session, _base_url(request, found.origin))
    return Response(
        ics.calendar(events),
        media_type=MEDIA,
        headers={"Cache-Control": "private, max-age=900", "X-Content-Type-Options": "nosniff"},
    )


class CalendarTokenOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    last_used_at: datetime | None


class CalendarTokenCreated(CalendarTokenOut):
    # Montrée une seule fois : seule l'empreinte du jeton est gardée.
    url: str


class CalendarTokenIn(BaseModel):
    name: Annotated[str, Field(max_length=60)] = "Mon agenda"
    # Adresse de la plateforme vue par le navigateur (location.origin).
    origin: Annotated[str, Field(max_length=200)] | None = None


@router.get("/agenda/tokens", operation_id="listCalendarTokens")
async def list_tokens(request: Request) -> list[CalendarTokenOut]:
    async with _runtime(request).sessionmaker() as session:
        rows = await session.scalars(
            select(CalendarToken)
            .where(CalendarToken.revoked_at.is_(None))
            .order_by(CalendarToken.created_at)
        )
        return [
            CalendarTokenOut(
                id=r.id, name=r.name, created_at=r.created_at, last_used_at=r.last_used_at
            )
            for r in rows
        ]


@router.post(
    "/agenda/tokens", operation_id="createCalendarToken", status_code=status.HTTP_201_CREATED
)
async def create_token(request: Request, body: CalendarTokenIn) -> CalendarTokenCreated:
    async with _runtime(request).sessionmaker.begin() as session:
        origin = body.origin if body.origin and ORIGIN.match(body.origin) else None
        row, token = await agenda.create_token(session, body.name.strip() or "Mon agenda", origin)
        await session.flush()
        await session.refresh(row)
        return CalendarTokenCreated(
            id=row.id,
            name=row.name,
            created_at=row.created_at,
            last_used_at=None,
            url=f"{_base_url(request, origin)}/api/agenda/feed/{token}.ics",
        )


@router.delete(
    "/agenda/tokens/{token_id}",
    operation_id="revokeCalendarToken",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_token(request: Request, token_id: int) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        row = await session.get(CalendarToken, token_id)
        if row is not None and row.revoked_at is None:
            row.revoked_at = datetime.now(UTC)
