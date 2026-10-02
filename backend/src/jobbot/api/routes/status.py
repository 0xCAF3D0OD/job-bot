"""État de la plateforme et dernières exécutions de tâches (page État)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from jobbot.db.models import JobRun, JobRunStatus
from jobbot.health import check_database
from jobbot.runtime import Runtime
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


class StatusResponse(BaseModel):
    version: str
    env: str
    database: DatabaseStatus
    worker: WorkerStatus


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


@router.get("/status", operation_id="getStatus")
async def get_status(request: Request) -> StatusResponse:
    runtime = _runtime(request)
    check = await check_database(runtime.engine)
    last_heartbeat: datetime | None = None
    if check.up_to_date:
        async with runtime.sessionmaker() as session:
            last_heartbeat = await session.scalar(
                select(JobRun.finished_at)
                .where(JobRun.job == HEARTBEAT_JOB, JobRun.status == JobRunStatus.SUCCESS)
                .order_by(JobRun.finished_at.desc())
                .limit(1)
            )
    stale_after = timedelta(seconds=HEARTBEAT_STALE_AFTER_SECONDS)
    healthy = last_heartbeat is not None and datetime.now(UTC) - last_heartbeat < stale_after
    return StatusResponse(
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
    )


@router.get("/job-runs", operation_id="listJobRuns")
async def list_job_runs(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    job: str | None = None,
) -> list[JobRunOut]:
    runtime = _runtime(request)
    query = select(JobRun).order_by(JobRun.started_at.desc(), JobRun.id.desc()).limit(limit)
    if job is not None:
        query = query.where(JobRun.job == job)
    async with runtime.sessionmaker() as session:
        rows = (await session.scalars(query)).all()
    return [JobRunOut.model_validate(row) for row in rows]
