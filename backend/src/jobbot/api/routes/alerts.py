"""Mes alertes (docs/20 §1) : recherches à suivre, liens par site, état d'après le journal."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from jobbot.alerts import service
from jobbot.db.models import AlertSearch, AlertSetup, Site
from jobbot.runtime import Runtime

# /api/alerts/refresh (bouton « Collecter ») existe déjà : préfixe distinct.
router = APIRouter(prefix="/api/alert-searches", tags=["alerts"])

Terms = Annotated[str, Field(min_length=1, max_length=120)]
Place = Annotated[str, Field(max_length=80)]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class AlertCell(BaseModel):
    site: str
    # Recherche déjà remplie sur le site (page du site pour un site ajouté), ou rien.
    url: str | None
    status: Literal["received", "created", "todo"]
    received_at: datetime | None
    created_at: datetime | None


class AlertSearchOut(BaseModel):
    id: int
    terms: str
    location: str | None
    active: bool
    cells: list[AlertCell]


class AlertSite(BaseModel):
    slug: str
    name: str
    # Adresses d'expédition, pour écrire le filtre de transfert.
    senders: list[str]
    # Recherche pré-remplie possible (jobup, jobs.ch, LinkedIn, Indeed).
    prefilled: bool


class AlertsPage(BaseModel):
    # Boîte lue par la plateforme (adresse et dossier), si la collecte est configurée.
    mailbox: str | None
    folder: str | None
    sites: list[AlertSite]
    searches: list[AlertSearchOut]


class AlertSearchIn(BaseModel):
    terms: Terms
    location: Place | None = None


class AlertSearchUpdate(BaseModel):
    terms: Terms | None = None
    location: Place | None = None
    active: bool | None = None


async def _page(runtime: Runtime) -> AlertsPage:
    settings = runtime.settings
    async with runtime.sessionmaker.begin() as session:
        await service.propose(session)
        await session.flush()
        sites = list(
            await session.scalars(select(Site).where(Site.active.is_(True)).order_by(Site.id))
        )
        searches = list(
            await session.scalars(
                select(AlertSearch).order_by(AlertSearch.active.desc(), AlertSearch.id)
            )
        )
        rows = [(s, await service.cells(session, s, sites)) for s in searches]
    return AlertsPage(
        mailbox=settings.imap_user or None if settings.imap_configured else None,
        folder=settings.imap_folder if settings.imap_configured else None,
        sites=[
            AlertSite(
                slug=s.slug,
                name=s.name,
                senders=list(s.senders or []),
                prefilled=s.slug in service.SEARCH_URLS,
            )
            for s in sites
        ],
        searches=[
            AlertSearchOut(
                id=s.id,
                terms=s.terms,
                location=s.location,
                active=s.active,
                cells=[AlertCell(**c.__dict__) for c in found],
            )
            for s, found in rows
        ],
    )


@router.get("", operation_id="listAlertSearches")
async def list_alert_searches(request: Request) -> AlertsPage:
    return await _page(_runtime(request))


@router.post("", operation_id="addAlertSearch", status_code=status.HTTP_201_CREATED)
async def add_alert_search(request: Request, body: AlertSearchIn) -> AlertsPage:
    async with _runtime(request).sessionmaker.begin() as session:
        session.add(
            AlertSearch(
                terms=" ".join(body.terms.split()),
                location=" ".join((body.location or "").split()) or None,
            )
        )
    return await _page(_runtime(request))


@router.patch("/{search_id}", operation_id="updateAlertSearch")
async def update_alert_search(
    request: Request, search_id: int, body: AlertSearchUpdate
) -> AlertsPage:
    async with _runtime(request).sessionmaker.begin() as session:
        search = await session.get(AlertSearch, search_id)
        if search is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "recherche introuvable")
        if body.terms is not None:
            search.terms = " ".join(body.terms.split())
        if body.location is not None:
            search.location = " ".join(body.location.split()) or None
        if body.active is not None:
            search.active = body.active
    return await _page(_runtime(request))


@router.delete("/{search_id}", operation_id="deleteAlertSearch")
async def delete_alert_search(request: Request, search_id: int) -> AlertsPage:
    async with _runtime(request).sessionmaker.begin() as session:
        search = await session.get(AlertSearch, search_id)
        if search is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "recherche introuvable")
        await session.delete(search)
    return await _page(_runtime(request))


@router.put("/{search_id}/sites/{site}", operation_id="markAlertCreated")
async def mark_alert_created(request: Request, search_id: int, site: str) -> AlertsPage:
    """« J'ai créé l'alerte » sur ce site."""
    async with _runtime(request).sessionmaker.begin() as session:
        if await session.get(AlertSearch, search_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "recherche introuvable")
        if await session.scalar(select(Site.id).where(Site.slug == site)) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "site inconnu")
        if await session.get(AlertSetup, (search_id, site)) is None:
            session.add(AlertSetup(search_id=search_id, site=site))
    return await _page(_runtime(request))


@router.delete("/{search_id}/sites/{site}", operation_id="unmarkAlertCreated")
async def unmark_alert_created(request: Request, search_id: int, site: str) -> AlertsPage:
    async with _runtime(request).sessionmaker.begin() as session:
        setup = await session.get(AlertSetup, (search_id, site))
        if setup is not None:
            await session.delete(setup)
    return await _page(_runtime(request))
