from collections.abc import Iterator

import pytest
from sqlalchemy import select

from jobbot.__main__ import main
from jobbot.db.models import JobRun
from jobbot.db.schema import head_revision
from jobbot.runtime import Runtime
from jobbot.settings import Settings
from jobbot.worker.app import build_procrastinate_app
from jobbot.worker.jobs import JOBS, RunContext, execute, register

from .conftest import TEST_DATABASE_URL, make_settings


async def _runs(runtime: Runtime, job: str) -> list[JobRun]:
    async with runtime.sessionmaker() as session:
        return list((await session.scalars(select(JobRun).where(JobRun.job == job))).all())


@pytest.mark.usefixtures("clean_job_runs")
async def test_heartbeat_records_a_successful_run(runtime: Runtime) -> None:
    assert await execute(runtime, "heartbeat") is True
    [run] = await _runs(runtime, "heartbeat")
    assert run.status == "success"
    assert run.finished_at is not None
    assert (run.items_in, run.items_out, run.error) == (0, 0, None)


@pytest.fixture
def failing_job() -> Iterator[str]:
    name = "test_failing"

    @register(name)
    async def fail(runtime: Runtime, ctx: RunContext) -> None:
        ctx.items_in = 3
        raise RuntimeError("panne simulée")

    yield name
    del JOBS[name]


@pytest.mark.usefixtures("clean_job_runs")
async def test_failure_is_recorded_then_raised(runtime: Runtime, failing_job: str) -> None:
    with pytest.raises(RuntimeError):
        await execute(runtime, failing_job)
    [run] = await _runs(runtime, failing_job)
    assert run.status == "failure"
    assert run.items_in == 3
    assert run.error == "RuntimeError: panne simulée"


def test_scheduler_can_be_disabled(settings: Settings) -> None:
    runtime = Runtime.create(settings)
    enabled = build_procrastinate_app(runtime)
    periodic = enabled.periodic_registry.periodic_tasks.values()
    assert sorted(t.periodic_id for t in periodic) == [
        "collect",
        "heartbeat",
        "news",
        "reminders",
        "score",
    ]
    disabled = build_procrastinate_app(Runtime.create(make_settings(scheduler_enabled=False)))
    assert {"collect", "heartbeat"} <= set(disabled.tasks)
    assert not disabled.periodic_registry.periodic_tasks


@pytest.fixture
def cli_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JOBBOT_DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("JOBBOT_LOG_LEVEL", "WARNING")


@pytest.mark.usefixtures("cli_env")
def test_run_job_cli_exit_codes(failing_job: str) -> None:
    assert main(["run-job", "heartbeat"]) == 0
    assert main(["run-job", failing_job]) == 1
    assert main(["run-job", "inconnue"]) == 1


@pytest.mark.usefixtures("cli_env")
def test_check_cli(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check"]) == 0
    assert f"migration {head_revision()} à jour" in capsys.readouterr().out
