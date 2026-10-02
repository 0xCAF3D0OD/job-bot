from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from structlog.testing import capture_logs

from jobbot.db.schema import head_revision
from jobbot.runtime import Runtime
from jobbot.worker.jobs import execute


async def test_healthz_does_not_need_database(offline_client: AsyncClient) -> None:
    response = await offline_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readyz_503_when_database_unreachable(offline_client: AsyncClient) -> None:
    response = await offline_client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["reason"] == "base de données injoignable"


async def test_readyz_200_when_migrated(client: AsyncClient) -> None:
    response = await client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "revision": head_revision()}


@pytest.fixture
async def outdated_schema(runtime: Runtime) -> AsyncIterator[None]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("UPDATE alembic_version SET version_num = '0001'"))
    yield
    async with runtime.engine.begin() as conn:
        await conn.execute(
            text("UPDATE alembic_version SET version_num = :head"), {"head": head_revision()}
        )


@pytest.mark.usefixtures("outdated_schema")
async def test_readyz_503_when_migration_missing(client: AsyncClient) -> None:
    response = await client.get("/readyz")
    assert response.status_code == 503
    assert "jobbot migrate" in response.json()["reason"]


async def test_version(client: AsyncClient) -> None:
    response = await client.get("/version")
    assert response.json() == {"version": "test", "migration_head": head_revision()}


@pytest.mark.usefixtures("clean_job_runs")
async def test_status_worker_unhealthy_without_heartbeat(client: AsyncClient) -> None:
    body = (await client.get("/api/status")).json()
    assert body["database"]["ok"] is True
    assert body["database"]["up_to_date"] is True
    assert body["worker"] == {
        "healthy": False,
        "last_heartbeat_at": None,
        "stale_after_seconds": 600,
    }


@pytest.mark.usefixtures("clean_job_runs")
async def test_status_worker_healthy_after_heartbeat(client: AsyncClient, runtime: Runtime) -> None:
    assert await execute(runtime, "heartbeat")
    body = (await client.get("/api/status")).json()
    assert body["worker"]["healthy"] is True
    assert body["worker"]["last_heartbeat_at"] is not None


async def test_status_reports_unreachable_database(offline_client: AsyncClient) -> None:
    response = await offline_client.get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert body["database"]["ok"] is False
    assert body["database"]["error"] == "OperationalError"
    assert body["worker"]["healthy"] is False


async def test_metrics_use_route_template(client: AsyncClient) -> None:
    await client.get("/api/job-runs", params={"limit": 3, "job": "heartbeat"})
    text_metrics = (await client.get("/metrics")).text
    for name in (
        "jobbot_http_requests_total",
        "jobbot_http_request_duration_seconds",
        "jobbot_job_runs_total",
        "jobbot_job_duration_seconds",
        "jobbot_job_last_success_timestamp_seconds",
        "jobbot_db_up",
    ):
        assert name in text_metrics
    assert 'route="/api/job-runs"' in text_metrics
    assert "limit=3" not in text_metrics


async def test_request_id_is_echoed_or_generated(client: AsyncClient) -> None:
    echoed = await client.get("/healthz", headers={"X-Request-ID": "abc-123"})
    assert echoed.headers["X-Request-ID"] == "abc-123"
    replaced = await client.get("/healthz", headers={"X-Request-ID": "pas valide !"})
    assert replaced.headers["X-Request-ID"] != "pas valide !"
    assert len(replaced.headers["X-Request-ID"]) == 32


async def test_access_log_has_route_but_no_query_string(client: AsyncClient) -> None:
    with capture_logs() as logs:
        await client.get("/api/job-runs", params={"job": "secret-value"})
    access = [entry for entry in logs if entry["event"] == "http_request"]
    assert access and access[0]["route"] == "/api/job-runs"
    assert "request_id" not in access[0] or access[0]["request_id"]
    assert "secret-value" not in repr(logs)
