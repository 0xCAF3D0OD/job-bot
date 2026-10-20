"""Application FastAPI.

Routes métier sous /api (le frontend les appelle en chemin relatif) ;
/healthz, /readyz, /metrics et /version à la racine pour l'exploitation.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from jobbot import demo
from jobbot.api.middleware import RequestContextMiddleware, SecurityMiddleware
from jobbot.api.routes import (
    account,
    agenda,
    alerts,
    applications,
    assistant,
    auth,
    certificates,
    collect,
    contacts,
    cvs,
    extension,
    inbox,
    insights,
    interviews,
    letters,
    maintenance,
    manual_offers,
    news,
    orp,
    orp_meeting,
    platform,
    preferences,
    profile,
    profiles,
    registry,
    rhythm,
    scoring,
    sites,
    spontaneous,
    status,
    today,
    trainings,
    welcome,
)
from jobbot.auth.middleware import AuthMiddleware
from jobbot.db.base import connected_as_admin
from jobbot.db.schema import head_revision
from jobbot.health import health_router
from jobbot.log import get_logger
from jobbot.maintenance import MaintenanceMiddleware, Watch
from jobbot.runtime import Runtime
from jobbot.settings import Settings

log = get_logger(__name__)


async def _check_access(runtime: Runtime) -> None:
    """L'API ne devrait jamais se connecter en administrateur (docs/78 §3.1) : la démo refuse
    de démarrer, une plateforme le dit dans son journal et à l'exploitant."""
    try:
        async with runtime.sessionmaker() as session:
            admin = await connected_as_admin(session)
    except SQLAlchemyError:
        return  # base injoignable : l'état le dira
    if not admin:
        return
    if runtime.settings.demo:
        raise demo.NotADemoDatabase(
            "la démo se connecte à la base en administrateur : utiliser le rôle jobbot_app"
        )
    log.warning("database_admin_connection", hint="JOBBOT_DATABASE_URL avec le rôle jobbot_app")


def create_app(settings: Settings, runtime: Runtime | None = None) -> FastAPI:
    runtime = runtime or Runtime.create(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.demo:
            # Garde-fou (docs/72 §2) : jamais le mode démo sur une base qui a un vrai compte.
            await demo.check(runtime.sessionmaker)
        await _check_access(runtime)
        yield
        await runtime.dispose()

    # En prod, la documentation interactive est masquée ; le schéma reste générable
    # hors ligne par `jobbot openapi` pour le frontend.
    docs = not settings.is_prod
    app = FastAPI(
        title="jobA1",
        version=settings.version,
        lifespan=lifespan,
        docs_url="/api/docs" if docs else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if docs else None,
    )
    app.state.runtime = runtime
    app.state.maintenance = Watch()

    # Ajouté avant le contexte de requête : celui-ci l'enveloppe et journalise aussi les refus.
    # À l'intérieur de la connexion : il sait si la requête vient de l'exploitant (docs/79).
    app.add_middleware(MaintenanceMiddleware, only="announced")
    app.add_middleware(AuthMiddleware)
    # Avant la connexion, qui lit la base : une base pas encore à jour répond « maintenance »
    # plutôt qu'une erreur (docs/81 §2).
    app.add_middleware(MaintenanceMiddleware, only="update")
    app.add_middleware(RequestContextMiddleware)
    # Le plus à l'extérieur : ses en-têtes vont aussi sur les refus des autres.
    app.add_middleware(SecurityMiddleware)
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
    app.include_router(maintenance.router)
    app.include_router(platform.router)
    app.include_router(account.router)
    app.include_router(welcome.router)
    app.include_router(assistant.router)
    app.include_router(extension.router)
    app.include_router(extension.tokens_router)
    app.include_router(contacts.router)
    app.include_router(spontaneous.router)
    app.include_router(manual_offers.router)
    app.include_router(agenda.router)
    app.include_router(status.router)
    app.include_router(collect.router)
    app.include_router(preferences.router)
    app.include_router(profile.router)
    app.include_router(scoring.router)
    app.include_router(applications.router)
    app.include_router(letters.router)
    app.include_router(cvs.router)
    app.include_router(orp.router)
    app.include_router(orp_meeting.router)
    app.include_router(certificates.router)
    app.include_router(rhythm.router)
    app.include_router(today.router)
    app.include_router(insights.router)
    app.include_router(registry.router)
    app.include_router(sites.router)
    app.include_router(inbox.router)
    app.include_router(news.router)
    app.include_router(trainings.router)
    app.include_router(profiles.router)
    app.include_router(alerts.router)
    app.include_router(interviews.router)
    return app
