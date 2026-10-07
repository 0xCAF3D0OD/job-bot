"""Application FastAPI.

Routes métier sous /api (le frontend les appelle en chemin relatif) ;
/healthz, /readyz, /metrics et /version à la racine pour l'exploitation.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jobbot.api.middleware import RequestContextMiddleware
from jobbot.api.routes import (
    alerts,
    applications,
    assistant,
    auth,
    collect,
    cvs,
    inbox,
    interviews,
    letters,
    news,
    orp,
    preferences,
    profile,
    profiles,
    registry,
    scoring,
    sites,
    status,
    today,
    trainings,
)
from jobbot.auth.middleware import AuthMiddleware
from jobbot.db.schema import head_revision
from jobbot.health import health_router
from jobbot.runtime import Runtime
from jobbot.settings import Settings


def create_app(settings: Settings, runtime: Runtime | None = None) -> FastAPI:
    runtime = runtime or Runtime.create(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await runtime.dispose()

    # En prod, la documentation interactive est masquée ; le schéma reste générable
    # hors ligne par `jobbot openapi` pour le frontend.
    docs = not settings.is_prod
    app = FastAPI(
        title="job-bot",
        version=settings.version,
        lifespan=lifespan,
        docs_url="/api/docs" if docs else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if docs else None,
    )
    app.state.runtime = runtime

    # Ajouté avant le contexte de requête : celui-ci l'enveloppe et journalise aussi les refus.
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RequestContextMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router())

    @app.get("/version", include_in_schema=False)
    async def version() -> dict[str, str | None]:
        return {"version": settings.version, "migration_head": head_revision()}

    app.include_router(auth.router)
    app.include_router(assistant.router)
    app.include_router(status.router)
    app.include_router(collect.router)
    app.include_router(preferences.router)
    app.include_router(profile.router)
    app.include_router(scoring.router)
    app.include_router(applications.router)
    app.include_router(letters.router)
    app.include_router(cvs.router)
    app.include_router(orp.router)
    app.include_router(today.router)
    app.include_router(registry.router)
    app.include_router(sites.router)
    app.include_router(inbox.router)
    app.include_router(news.router)
    app.include_router(trainings.router)
    app.include_router(profiles.router)
    app.include_router(alerts.router)
    app.include_router(interviews.router)
    return app
