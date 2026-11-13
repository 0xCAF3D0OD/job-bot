"""A1 du 13 novembre : une tâche laissée « en cours » par un worker tué est reprise une fois, sans
double exécution, et un arrêt propre relâche la tâche en cours."""

import asyncio
from collections.abc import AsyncIterator

import procrastinate
import pytest
from sqlalchemy import text

from jobbot.runtime import Runtime
from jobbot.scoring import service
from jobbot.worker.app import build_procrastinate_app
from jobbot.worker.recovery import recover_stalled

from .conftest import admin_engine
from .test_scoring import FakeClient, add_offer, ai, evaluation, fake  # noqa: F401


@pytest.fixture
async def papp(runtime: Runtime) -> AsyncIterator[procrastinate.App]:
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM procrastinate_jobs"))
        await conn.execute(text("DELETE FROM procrastinate_workers"))
    app = build_procrastinate_app(runtime)
    async with app.open_async():
        yield app
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM procrastinate_jobs"))
        await conn.execute(text("DELETE FROM procrastinate_workers"))


async def killed_while_running(app: procrastinate.App, task: str, queueing_lock: str) -> int:
    """Une tâche prise par un worker, puis le worker tué : plus de signe de vie depuis 5 min."""
    job_id = await app.configure_task(task, lock=task, queueing_lock=queueing_lock).defer_async()
    worker = await app.job_manager.register_worker()
    job = await app.job_manager.fetch_job(queues=None, worker_id=worker)
    assert job is not None and job.id == job_id
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("UPDATE procrastinate_workers SET last_heartbeat = now() - interval '5 minutes'")
        )
    return job_id


async def statuses() -> list[tuple[str, str]]:
    async with admin_engine().begin() as conn:
        rows = await conn.execute(
            text("SELECT task_name, status::text FROM procrastinate_jobs ORDER BY id")
        )
        return [(r[0], r[1]) for r in rows]


async def test_stalled_lock_blocks_until_recovered(papp: procrastinate.App) -> None:
    await killed_while_running(papp, "cv_read", "cv_read:7")
    # Sans reprise : le verrou « cv_read » bloque toute nouvelle lecture, à jamais.
    await papp.configure_task("cv_read", lock="cv_read", queueing_lock="cv_read:8").defer_async()
    live = await papp.job_manager.register_worker()
    assert await papp.job_manager.fetch_job(queues=None, worker_id=live) is None

    assert await recover_stalled(papp) == (1, 0)
    first = await papp.job_manager.fetch_job(queues=None, worker_id=live)
    assert first is not None and first.queueing_lock == "cv_read:7"
    # Un seul exemplaire repris : un second contrôle ne la remet pas en file.
    assert await recover_stalled(papp) == (0, 0)


async def test_stalled_job_already_queued_again_is_closed_not_doubled(
    papp: procrastinate.App,
) -> None:
    await killed_while_running(papp, "score", "score")
    # Le planificateur a remis « score » en file entre-temps (même verrou de file).
    await papp.configure_task("score", lock="score", queueing_lock="score").defer_async()
    assert await recover_stalled(papp) == (0, 1)
    assert await statuses() == [("score", "failed"), ("score", "todo")]


async def test_rerun_after_recovery_scores_only_what_is_left(
    papp: procrastinate.App,
    ai: Runtime,  # noqa: F811
    fake: FakeClient,  # noqa: F811
) -> None:
    done = await add_offer(ai, 1)
    await service.run_scoring(ai)  # la note de la première offre, faite avant la coupure
    left = await add_offer(ai, 2)
    await killed_while_running(papp, "score", "score")
    assert await recover_stalled(papp) == (1, 0)
    await service.run_scoring(ai)  # la tâche reprise
    assert len(fake.calls) == 2  # une note par offre, pas de double appel
    assert (await evaluation(ai, done)).score == 78  # type: ignore[union-attr]
    assert (await evaluation(ai, left)).score == 78  # type: ignore[union-attr]


async def test_clean_stop_releases_the_running_task(papp: procrastinate.App) -> None:
    started = asyncio.Event()

    @papp.task(name="test_lente", lock="test_lente", queue="default")
    async def slow() -> None:
        started.set()
        await asyncio.sleep(60)

    await papp.configure_task("test_lente").defer_async()
    worker = asyncio.create_task(
        papp.run_worker_async(
            queues=["default"], install_signal_handlers=False, shutdown_graceful_timeout=0.2
        )
    )
    await asyncio.wait_for(started.wait(), timeout=10)
    worker.cancel()  # ce que fait run_worker au signal d'arrêt
    await asyncio.gather(worker, return_exceptions=True)
    # (le planificateur a pu mettre ses tâches en file pendant ce temps)
    assert [s for s in await statuses() if s[0] == "test_lente"] == [("test_lente", "aborted")]
    # Verrou relâché : la tâche suivante du même nom est prise.
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM procrastinate_jobs WHERE task_name <> 'test_lente'"))
    await papp.configure_task("test_lente").defer_async()
    live = await papp.job_manager.register_worker()
    job = await papp.job_manager.fetch_job(queues=None, worker_id=live)
    assert job is not None and job.task_name == "test_lente"
