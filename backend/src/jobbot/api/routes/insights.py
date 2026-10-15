"""Bilan de ta recherche (docs/42) : ce qui donne des réponses, et le résumé pour l'ORP."""

import calendar
from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel

from jobbot.core.orp import LOCAL_TZ, shift_month
from jobbot.insights import service
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["insights"])
MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"


class FunnelOut(BaseModel):
    received: int
    retained: int
    applications: int
    responses: int
    interviews: int
    engagements: int


class DelayOut(BaseModel):
    # Jours entre l'envoi et la réponse : médiane, plus court, plus long.
    typical: int
    shortest: int
    longest: int


class GroupOut(BaseModel):
    key: str
    label: str
    responses: int
    total: int
    # Faux sous 5 candidatures : « trop peu pour conclure ».
    enough: bool


class ComparisonOut(BaseModel):
    key: Literal["source", "score", "contact", "follow_up"]
    title: str
    groups: list[GroupOut]


class BucketOut(BaseModel):
    # Premier jour du mois, ou de la semaine (coupée au mois choisi).
    start: date
    applications: int
    responses: int


class SearchReportOut(BaseModel):
    start: date | None
    end: date
    funnel: FunnelOut
    delay: DelayOut | None
    comparisons: list[ComparisonOut]
    # Une phrase seulement si un écart est net (docs/42 §2).
    headline: str | None
    # Pour un mois choisi : le résumé à copier pour le rendez-vous ORP (docs/42 §3).
    orp_summary: str | None
    # « Par mois » (docs/55) : mois de la période, ou semaines d'un mois choisi.
    unit: Literal["month", "week"] = "month"
    buckets: list[BucketOut] = []
    # Entretiens encore à venir, parmi les candidatures de la période.
    interviews_upcoming: int = 0


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


@router.get("/insights", operation_id="getInsights")
async def get_insights(
    request: Request,
    period: Literal["recent", "month", "all"] = "recent",
    month: Annotated[str | None, Query(pattern=MONTH)] = None,
) -> SearchReportOut:
    today = datetime.now(UTC).astimezone(LOCAL_TZ).date()
    current = f"{today:%Y-%m}"
    start: date | None
    if period == "month":
        if month is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "mois manquant")
        year, number = (int(x) for x in month.split("-"))
        start = date(year, number, 1)
        end = min(date(year, number, calendar.monthrange(year, number)[1]), today)
    elif period == "all":
        start, end = None, today
    else:
        # Les 3 derniers mois : le mois en cours et les deux précédents.
        start, end = date.fromisoformat(f"{shift_month(current, -2)}-01"), today
    async with _runtime(request).sessionmaker() as session:
        found = await service.insights(
            session, start, end, "week" if period == "month" else "month"
        )
        summary = await service.orp_summary(session, month) if period == "month" and month else None
    return SearchReportOut(
        start=start,
        end=end,
        funnel=FunnelOut(**vars(found.funnel)),
        delay=DelayOut(**vars(found.delay)) if found.delay else None,
        comparisons=[
            ComparisonOut(
                key=c.key,
                title=c.title,
                groups=[
                    GroupOut(
                        key=g.key,
                        label=g.label,
                        responses=g.responses,
                        total=g.total,
                        enough=g.enough,
                    )
                    for g in c.groups
                ],
            )
            for c in found.comparisons
        ],
        headline=found.headline,
        orp_summary=summary,
        unit="week" if found.unit == "week" else "month",
        buckets=[BucketOut(**vars(b)) for b in found.buckets],
        interviews_upcoming=found.interviews_upcoming,
    )
