"""État de la plateforme et dernières exécutions de tâches (page État)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts
from jobbot.api.owner import require_owner
from jobbot.db.models import JobRun, JobRunStatus
from jobbot.health import check_database
from jobbot.runtime import Runtime
from jobbot.worker.tasks.collect import COLLECT_JOB
from jobbot.worker.tasks.heartbeat import HEARTBEAT_JOB, HEARTBEAT_STALE_AFTER_SECONDS

router = APIRouter(prefix="/api", tags=["status"])


class DatabaseStatus(BaseModel):
    ok: bool
    revision: str | None
    head: str | None
    up_to_date: bool
    error: str | None


class WorkerStatus(BaseModel):
    healthy: bool
    last_heartbeat_at: datetime | None
    stale_after_seconds: int


class CollectStatus(BaseModel):
    configured: bool
    last_success_at: datetime | None
    last_failure_at: datetime | None
    # Erreur de la dernière exécution, si elle a échoué.
    last_error: str | None


class StatusResponse(BaseModel):
    # La plateforme répond : base joignable et à jour, worker en vie.
    ok: bool
    # Le détail technique, pour l'exploitant seulement (docs/108 §3) ; vide pour un compte
    # invité, qui ne voit que `ok` et la collecte.
    version: str | None = None
    env: str | None = None
    database: DatabaseStatus | None = None
    worker: WorkerStatus | None = None
    collect: CollectStatus


class JobRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job: str
    run_id: uuid.UUID
    started_at: datetime
    finished_at: datetime | None
    status: JobRunStatus
    items_in: int | None
    items_out: int | None
    error: str | None


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


async def _last_finished(session: AsyncSession, job: str, status: JobRunStatus) -> datetime | None:
    return await session.scalar(
        select(JobRun.finished_at)
        .where(JobRun.job == job, JobRun.status == status)
        .order_by(JobRun.finished_at.desc())
        .limit(1)
    )


@router.get("/status", operation_id="getStatus")
async def get_status(request: Request) -> StatusResponse:
    runtime = _runtime(request)
    check = await check_database(runtime.engine)
    last_heartbeat: datetime | None = None
    # Base injoignable : on ne sait pas qui demande ; le détail reste visible (un compte
    # connecté seulement), sinon l'exploitant ne pourrait plus rien diagnostiquer.
    owner = True
    collect = CollectStatus(
        configured=runtime.settings.imap_configured,
        last_success_at=None,
        last_failure_at=None,
        last_error=None,
    )
    if check.up_to_date:
        async with runtime.sessionmaker() as session:
            last_heartbeat = await _last_finished(session, HEARTBEAT_JOB, JobRunStatus.SUCCESS)
            collect.last_success_at = await _last_finished(
                session, COLLECT_JOB, JobRunStatus.SUCCESS
            )
            collect.last_failure_at = await _last_finished(
                session, COLLECT_JOB, JobRunStatus.FAILURE
            )
            latest = await session.scalar(
                select(JobRun)
                .where(JobRun.job == COLLECT_JOB, JobRun.status != JobRunStatus.RUNNING)
                .order_by(JobRun.finished_at.desc())
                .limit(1)
            )
            # Le message d'erreur peut citer la boîte de l'exploitant ou un autre compte : à lui
            # seul (docs/69 §1) ; les autres voient l'échec, sans le détail.
            owner = await accounts.is_owner(session)
            if latest is not None and latest.status == JobRunStatus.FAILURE:
                collect.last_error = latest.error if owner else "voir avec l'exploitant"
    stale_after = timedelta(seconds=HEARTBEAT_STALE_AFTER_SECONDS)
    healthy = last_heartbeat is not None and datetime.now(UTC) - last_heartbeat < stale_after
    ok = check.ok and check.up_to_date and healthy
    if not owner:
        return StatusResponse(ok=ok, collect=collect)
    return StatusResponse(
        ok=ok,
        version=runtime.settings.version,
        env=runtime.settings.env.value,
        database=DatabaseStatus(
            ok=check.ok,
            revision=check.revision,
            head=check.head,
            up_to_date=check.up_to_date,
            error=check.error,
        ),
        worker=WorkerStatus(
            healthy=healthy,
            last_heartbeat_at=last_heartbeat,
            stale_after_seconds=HEARTBEAT_STALE_AFTER_SECONDS,
        ),
        collect=collect,
    )


@router.get("/job-runs", operation_id="listJobRuns")
async def list_job_runs(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    job: str | None = None,
) -> list[JobRunOut]:
    """Le journal des tâches, commun à tous les comptes : réservé à l'exploitant (docs/69 §1)."""
    runtime = _runtime(request)
    await require_owner(runtime)
    query = select(JobRun).order_by(JobRun.started_at.desc(), JobRun.id.desc()).limit(limit)
    if job is not None:
        query = query.where(JobRun.job == job)
    async with runtime.sessionmaker() as session:
        rows = (await session.scalars(query)).all()
    return [JobRunOut.model_validate(row) for row in rows]
