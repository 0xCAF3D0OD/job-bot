"""Contrôles de santé communs à l'API et au worker (/healthz, /readyz)."""

from dataclasses import dataclass

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from jobbot.db.schema import current_revision, head_revision
from jobbot.log import get_logger
from jobbot.metrics import DB_UP

log = get_logger(__name__)


@dataclass
class DatabaseCheck:
    ok: bool
    revision: str | None
    head: str | None
    error: str | None = None

    @property
    def up_to_date(self) -> bool:
        return self.ok and self.revision is not None and self.revision == self.head


async def check_database(engine: AsyncEngine) -> DatabaseCheck:
    head = head_revision()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            revision = await current_revision(conn)
    except Exception as exc:
        DB_UP.set(0)
        # Seul le type d'erreur est exposé : le message peut contenir l'hôte ou l'utilisateur.
        log.warning("database_unreachable", error=type(exc).__name__)
        return DatabaseCheck(ok=False, revision=None, head=head, error=type(exc).__name__)
    DB_UP.set(1)
    return DatabaseCheck(ok=True, revision=revision, head=head)


def health_router() -> APIRouter:
    """Points d'entrée d'exploitation, hors de /api et sans authentification."""
    router = APIRouter(include_in_schema=False)

    @router.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/readyz")
    async def readyz(request: Request) -> JSONResponse:
        check = await check_database(request.app.state.runtime.engine)
        if not check.ok:
            reason = "base de données injoignable"
        elif not check.up_to_date:
            reason = (
                f"migration attendue {check.head}, trouvée {check.revision} : "
                "lancer `jobbot migrate`"
            )
        else:
            return JSONResponse({"status": "ready", "revision": check.revision})
        return JSONResponse({"status": "not_ready", "reason": reason}, status_code=503)

    @router.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return router
