"""Preuves ORP du mois : tableau, contrôle avant remise, CSV, remise (docs/09-export-orp.md).

Rien n'est transmis à l'ORP ni à Job-Room : Kevin remet lui-même le PDF ou recopie les lignes.
"""

from datetime import UTC, date, datetime, time
from typing import Annotated, Literal

from fastapi import APIRouter, Path, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import (
    LOCAL_TZ,
    ApplicationData,
    OrpRow,
    due_date,
    shift_month,
    to_csv,
    to_row,
)
from jobbot.db.models import Application, OrpMonth, Search, Setting
from jobbot.letters.service import load_identity
from jobbot.orp.service import load_due_day
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/orp", tags=["orp"])
Month = Annotated[str, Path(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


def _today() -> date:
    return datetime.now(UTC).astimezone(LOCAL_TZ).date()


class OrpRowOut(BaseModel):
    application_id: int
    date: str
    company: str
    address: str
    contact: str
    phone: str
    job_title: str
    rate: str
    method: str
    assigned: str
    result: str
    url: str
    missing: list[str]


class OrpSearchOut(BaseModel):
    received_at: datetime
    source: str
    label: str | None
    results_count: int


class OrpHolder(BaseModel):
    """En-tête du formulaire : nom et adresse saisis dans les Réglages."""

    name: str | None
    address: str | None


class OrpMonthOut(BaseModel):
    month: str
    state: Literal["en_cours", "a_remettre", "remis"]
    due_date: date
    count: int
    target: int | None
    incomplete: int
    rows: list[OrpRowOut]
    submitted_at: datetime | None
    exported_at: datetime | None
    changed_after_submit: bool
    holder: OrpHolder
    # Annexe facultative : alertes reçues dans le mois (journal des recherches).
    searches: list[OrpSearchOut]


async def mark_changed(session: AsyncSession, months: set[str]) -> None:
    """Une candidature d'un mois déjà remis a changé : la page le signalera."""
    for month in months:
        record = await session.get(OrpMonth, month)
        if record is not None and record.submitted_at is not None:
            record.changed_after_submit = True


async def _rows(session: AsyncSession, month: str) -> list[OrpRow]:
    applications = await session.scalars(
        select(Application)
        .where(Application.orp_month == month)
        .order_by(Application.sent_at, Application.id)
    )
    return [
        to_row(
            ApplicationData(
                id=a.id,
                sent_at=a.sent_at,
                company=a.company,
                company_address=a.company_address,
                contact_name=a.contact_name,
                contact_phone=a.contact_phone,
                job_title=a.job_title,
                rate_text=a.rate_text,
                method=a.method,
                assigned_by_orp=a.assigned_by_orp,
                status=a.status,
                status_reason=a.status_reason,
                interview_at=a.interview_at,
                application_url=a.application_url,
            )
        )
        for a in applications
    ]


async def _default_month(session: AsyncSession) -> str:
    """Le mois précédent tant qu'il n'est pas remis (s'il a des candidatures), sinon le mois
    en cours (docs/09 §2)."""
    current = f"{_today():%Y-%m}"
    previous = shift_month(current, -1)
    record = await session.get(OrpMonth, previous)
    if record is not None and record.submitted_at is not None:
        return current
    count = await session.scalar(
        select(func.count()).select_from(Application).where(Application.orp_month == previous)
    )
    return previous if count else current


def _bounds(month: str) -> tuple[datetime, datetime]:
    year, number = (int(x) for x in month.split("-"))
    start = datetime.combine(date(year, number, 1), time(), LOCAL_TZ)
    nyear, nnumber = (int(x) for x in shift_month(month, 1).split("-"))
    end = datetime.combine(date(nyear, nnumber, 1), time(), LOCAL_TZ)
    return start, end


@router.get("", operation_id="getOrpMonth")
async def get_orp_month(
    request: Request,
    month: Annotated[str | None, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")] = None,
) -> OrpMonthOut:
    async with _runtime(request).sessionmaker() as session:
        month = month or await _default_month(session)
        rows = await _rows(session, month)
        record = await session.get(OrpMonth, month)
        target = await session.scalar(
            select(Setting.value).where(Setting.key == "orp_monthly_target")
        )
        identity = await load_identity(session)
        due_day = await load_due_day(session)
        start, end = _bounds(month)
        searches = await session.scalars(
            select(Search)
            .where(Search.received_at >= start, Search.received_at < end)
            .order_by(Search.received_at)
        )
        search_rows = [
            OrpSearchOut(
                received_at=s.received_at,
                source=s.source,
                label=s.alert_label or s.subject,
                results_count=s.results_count,
            )
            for s in searches
        ]
    submitted_at = record.submitted_at if record else None
    current = f"{_today():%Y-%m}"
    state: Literal["en_cours", "a_remettre", "remis"] = (
        "remis" if submitted_at else ("a_remettre" if month < current else "en_cours")
    )
    city = " ".join(x for x in (identity.postcode, identity.city) if x)
    address = ", ".join(x for x in (identity.street, city) if x) or None
    return OrpMonthOut(
        month=month,
        state=state,
        due_date=due_date(month, due_day),
        count=len(rows),
        target=int(target) if target else None,
        incomplete=sum(1 for r in rows if r.missing),
        rows=[OrpRowOut(**r.__dict__) for r in rows],
        submitted_at=submitted_at,
        exported_at=record.exported_at if record else None,
        changed_after_submit=bool(record and record.changed_after_submit),
        holder=OrpHolder(name=identity.name, address=address),
        searches=search_rows,
    )


async def _touch(session: AsyncSession, month: str, **values: object) -> None:
    await session.execute(
        insert(OrpMonth)
        .values(month=month, **values)
        .on_conflict_do_update(index_elements=["month"], set_=values)
    )


@router.get(
    "/{month}/csv",
    operation_id="downloadOrpCsv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
async def download_orp_csv(request: Request, month: Month) -> Response:
    async with _runtime(request).sessionmaker.begin() as session:
        rows = await _rows(session, month)
        await _touch(session, month, exported_at=datetime.now(UTC))
    return Response(
        to_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="preuves-orp-{month}.csv"'},
    )


@router.post(
    "/{month}/exported", operation_id="markOrpExported", status_code=status.HTTP_204_NO_CONTENT
)
async def mark_exported(request: Request, month: Month) -> None:
    """Le PDF passe par l'impression du navigateur : l'interface signale l'export."""
    async with _runtime(request).sessionmaker.begin() as session:
        await _touch(session, month, exported_at=datetime.now(UTC))


@router.put(
    "/{month}/submission", operation_id="submitOrpMonth", status_code=status.HTTP_204_NO_CONTENT
)
async def submit_month(request: Request, month: Month) -> None:
    """« Marquer comme remis » : la remise est datée, les modifications repartent de zéro."""
    async with _runtime(request).sessionmaker.begin() as session:
        await _touch(session, month, submitted_at=datetime.now(UTC), changed_after_submit=False)


@router.delete(
    "/{month}/submission",
    operation_id="cancelOrpSubmission",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_submission(request: Request, month: Month) -> None:
    async with _runtime(request).sessionmaker.begin() as session:
        await _touch(session, month, submitted_at=None, changed_after_submit=False)
