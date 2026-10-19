"""Le bon rythme (docs/86, 0.68.1) : les semaines d'un mois, pour le Bilan."""

from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from jobbot.rhythm import service
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/rhythm", tags=["rhythm"])


class MonthWeekOut(BaseModel):
    start: str
    end: str
    target: int | None
    count: int
    state: Literal["done", "missed", "current", "upcoming", "pause"]


class MonthWeeksOut(BaseModel):
    month: str
    weeks: list[MonthWeekOut]


@router.get("/semaines", operation_id="getRhythmWeeks")
async def get_rhythm_weeks(
    request: Request, month: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")] = None
) -> MonthWeeksOut:
    runtime: Runtime = request.app.state.runtime
    today = service.local_today()
    wanted = month or f"{today:%Y-%m}"
    async with runtime.sessionmaker() as session:
        weeks = await service.month_weeks(session, wanted, today)
    return MonthWeeksOut(
        month=wanted,
        weeks=[
            MonthWeekOut(
                start=w.start.isoformat(),
                end=w.end.isoformat(),
                target=w.target,
                count=w.count,
                state=w.state,
            )
            for w in weeks
        ],
    )
