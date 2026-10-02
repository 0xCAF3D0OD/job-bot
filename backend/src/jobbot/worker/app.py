"""Processus worker : file procrastinate + petit serveur HTTP (/healthz, /readyz, /metrics).

Arrêt sur SIGTERM/SIGINT : la tâche en cours a SHUTDOWN_GRACE_SECONDS (20 s) pour finir,
puis le processus s'arrête.
Si la base est injoignable au démarrage, le worker attend (sans planter en boucle) :
/healthz répond 200 et /readyz 503 pendant ce temps.
"""

import asyncio
import contextlib
import signal
from typing import Any

import procrastinate
import psycopg
import uvicorn
from fastapi import FastAPI

from jobbot.health import health_router
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.settings import Settings
from jobbot.worker import tasks as _tasks  # noqa: F401  (enregistre les tâches)
from jobbot.worker.jobs import JOBS, execute

log = get_logger(__name__)

QUEUE = "default"
SHUTDOWN_GRACE_SECONDS = 20
DB_RETRY_MAX_SECONDS = 30


def build_procrastinate_app(runtime: Runtime) -> procrastinate.App:
    app = procrastinate.App(
        connector=procrastinate.PsycopgConnector(conninfo=runtime.settings.libpq_url)
    )
    for spec in JOBS.values():
        name = spec.name

        async def run(timestamp: int | None = None, _name: str = name) -> None:
            await execute(runtime, _name)

        task = app.task(name=name, queue=QUEUE)(run)
        if runtime.settings.scheduler_enabled and spec.cron:
            app.periodic(cron=spec.cron, periodic_id=name)(task)
    return app


def build_http_app(runtime: Runtime) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.runtime = runtime
    app.include_router(health_router())
    return app


async def _wait_for_database(settings: Settings, stop: asyncio.Event) -> bool:
    delay = 1.0
    while not stop.is_set():
        try:
            conn = await psycopg.AsyncConnection.connect(settings.libpq_url, connect_timeout=3)
            await conn.close()
            return True
        except psycopg.OperationalError:
            log.warning("database_unreachable_retrying", retry_in_s=delay)
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=delay)
            delay = min(delay * 2, DB_RETRY_MAX_SECONDS)
    return False


async def run_worker(settings: Settings) -> None:
    runtime = Runtime.create(settings)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    server = uvicorn.Server(
        uvicorn.Config(
            build_http_app(runtime),
            host=settings.api_host,
            port=settings.worker_http_port,
            log_config=None,
            access_log=False,
        )
    )
    # _serve() plutôt que serve() : serve() installe ses propres gestionnaires de signaux,
    # qui remplaceraient ceux du worker.
    http_task = asyncio.create_task(server._serve(), name="worker-http")
    log.info(
        "worker_starting",
        http_port=settings.worker_http_port,
        scheduler_enabled=settings.scheduler_enabled,
        jobs=sorted(JOBS),
    )

    try:
        if not await _wait_for_database(settings, stop):
            return
        papp = build_procrastinate_app(runtime)
        async with papp.open_async():
            worker_task: asyncio.Task[Any] = asyncio.create_task(
                papp.run_worker_async(
                    queues=[QUEUE],
                    install_signal_handlers=False,
                    shutdown_graceful_timeout=SHUTDOWN_GRACE_SECONDS,
                    # L'historique est dans job_runs : la file ne garde pas les tâches réussies.
                    delete_jobs="successful",
                ),
                name="procrastinate-worker",
            )
            stop_task = asyncio.create_task(stop.wait())
            await asyncio.wait(
                {worker_task, stop_task, http_task}, return_when=asyncio.FIRST_COMPLETED
            )
            # Sans signal d'arrêt, la fin du worker ou du serveur HTTP est une panne :
            # code retour 1 pour que l'orchestrateur relance le processus.
            crashed = not stop.is_set()
            log.info("worker_stopping", crashed=crashed)
            worker_task.cancel()
            stop_task.cancel()
            results = await asyncio.gather(worker_task, return_exceptions=True)
            if crashed:
                log.error("worker_crashed", error=repr(results[0]))
                raise SystemExit(1)
    finally:
        server.should_exit = True
        await asyncio.gather(http_task, return_exceptions=True)
        await runtime.dispose()
        log.info("worker_stopped")
