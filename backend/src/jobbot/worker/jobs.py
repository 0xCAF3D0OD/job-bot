"""Registre des tâches et suivi de chaque exécution (table job_runs + métriques + logs).

Une tâche est une fonction asynchrone idempotente qui reçoit le Runtime et un RunContext.
Elle peut être exécutée par le worker (file procrastinate, éventuellement planifiée)
ou une seule fois par `jobbot run-job <nom>`.
"""

import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from zoneinfo import ZoneInfo

import structlog
from sqlalchemy import update

from jobbot import accounts
from jobbot.db.models import JobRun, JobRunStatus
from jobbot.log import get_logger
from jobbot.metrics import JOB_DURATION, JOB_LAST_SUCCESS, JOB_RUNS
from jobbot.runtime import Runtime

log = get_logger(__name__)


@dataclass
class RunContext:
    job: str
    run_id: uuid.UUID = field(default_factory=uuid.uuid4)
    items_in: int | None = None
    items_out: int | None = None


JobFunc = Callable[[Runtime, RunContext], Awaitable[None]]

# Pour qui tourne une tâche (docs/65 §7) : chaque compte à son tour ; l'exploitant seul (ce
# qui vient encore de l'installation : sa boîte e-mail) ; ou la plateforme (sans compte).
Scope = Literal["accounts", "owner", "platform"]

# Les plages horaires des tâches planifiées s'entendent en heure suisse ; le planificateur,
# lui, compte en UTC. La tâche est donc planifiée large et filtrée ici.
LOCAL_TZ = ZoneInfo("Europe/Zurich")


@dataclass(frozen=True)
class JobSpec:
    name: str
    func: JobFunc
    # Planification cron du worker (en UTC) ; ignorée si JOBBOT_SCHEDULER_ENABLED=false.
    cron: str | None = None
    # Heures (début, fin incluses, heure suisse) où une exécution planifiée est utile.
    # Les exécutions manuelles (bouton, `jobbot run-job`) ne sont pas limitées.
    active_hours: tuple[int, int] | None = None
    scope: Scope = "accounts"

    def is_active_at(self, moment: datetime) -> bool:
        if self.active_hours is None:
            return True
        start, end = self.active_hours
        return start <= moment.astimezone(LOCAL_TZ).hour <= end


JOBS: dict[str, JobSpec] = {}


def register(
    name: str,
    *,
    cron: str | None = None,
    active_hours: tuple[int, int] | None = None,
    scope: Scope = "accounts",
) -> Callable[[JobFunc], JobFunc]:
    def decorator(func: JobFunc) -> JobFunc:
        if name in JOBS:
            raise ValueError(f"Tâche déjà enregistrée : {name}")
        JOBS[name] = JobSpec(
            name=name, func=func, cron=cron, active_hours=active_hours, scope=scope
        )
        return func

    return decorator


async def execute(runtime: Runtime, name: str) -> bool:
    """Exécute la tâche, trace le résultat et renvoie True en cas de succès.

    Une erreur de la tâche est enregistrée puis relancée : procrastinate la marque en échec.
    """
    spec = JOBS[name]
    ctx = RunContext(job=name)
    started = time.monotonic()
    async with runtime.sessionmaker.begin() as session:
        session.add(JobRun(job=name, run_id=ctx.run_id, status=JobRunStatus.RUNNING))

    with structlog.contextvars.bound_contextvars(job=name, run_id=str(ctx.run_id)):
        log.info("job_started")
        status = JobRunStatus.SUCCESS
        error: str | None = None
        try:
            await _run_for_accounts(runtime, spec, ctx)
        except Exception as exc:
            status = JobRunStatus.FAILURE
            error = f"{type(exc).__name__}: {exc}"[:2000]
            log.exception("job_failed")
            raise
        finally:
            duration = time.monotonic() - started
            async with runtime.sessionmaker.begin() as session:
                await session.execute(
                    update(JobRun)
                    .where(JobRun.run_id == ctx.run_id)
                    .values(
                        status=status,
                        finished_at=datetime.now(UTC),
                        items_in=ctx.items_in,
                        items_out=ctx.items_out,
                        error=error,
                    )
                )
            JOB_RUNS.labels(job=name, status=status.value).inc()
            JOB_DURATION.labels(job=name).observe(duration)
            if status is JobRunStatus.SUCCESS:
                JOB_LAST_SUCCESS.labels(job=name).set(time.time())
                log.info(
                    "job_finished",
                    duration_s=round(duration, 3),
                    items_in=ctx.items_in,
                    items_out=ctx.items_out,
                )
    return status is JobRunStatus.SUCCESS


async def _run_for_accounts(runtime: Runtime, spec: JobSpec, ctx: RunContext) -> None:
    """Une tâche lancée pour un compte (bouton, tâche appelée par une autre) ne tourne que
    pour lui ; planifiée, elle passe par chaque compte, et l'échec de l'un n'arrête pas les
    suivants (la première erreur est relancée à la fin)."""
    if spec.scope == "platform":
        await spec.func(runtime, ctx)
        return
    async with runtime.sessionmaker.begin() as session:
        owner = await accounts.owner_id(session)
        everyone = await accounts.account_ids(session)
    current = accounts.current()
    if current is not None:
        if spec.scope == "accounts" or current == owner:
            await spec.func(runtime, ctx)
        return
    failure: Exception | None = None
    for account in [owner] if spec.scope == "owner" else everyone:
        with accounts.use(account), structlog.contextvars.bound_contextvars(account=account):
            try:
                await spec.func(runtime, ctx)
            except Exception as exc:
                log.exception("job_failed_for_account")
                failure = failure or exc
    if failure is not None:
        raise failure
