"""Mes alertes (docs/20 §1) : recherches à suivre, liens par site, état d'après le journal."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from jobbot import accounts, welcome
from jobbot.alerts import service
from jobbot.collect import public_search
from jobbot.core.filter import RemotePolicy
from jobbot.db.models import AlertSearch, AlertSetup, Search, Site
from jobbot.filtering.service import load_criteria
from jobbot.mail import addresses
from jobbot.runtime import Runtime
from jobbot.sources.sites import followed

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
    # Même recherche en télétravail (docs/26 §5), si tu l'acceptes et si le site le permet.
    remote_url: str | None = None


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


class ToConfirm(BaseModel):
    """Un site demande de confirmer l'alerte (docs/65 §3) : le lien est à ouvrir soi-même."""

    search_id: int
    site: str
    subject: str | None
    received_at: datetime
    url: str


class AlertsPage(BaseModel):
    # L'adresse à donner aux sites pour ce compte (docs/65 §3), si la collecte est configurée ;
    # le dossier lu, pour l'exploitant seulement (c'est sa boîte).
    mailbox: str | None
    folder: str | None
    # Adresse propre au compte (boite+code@…), et non la boîte de l'exploitant.
    personal_address: bool = False
    sites: list[AlertSite]
    searches: list[AlertSearchOut]
    to_confirm: list[ToConfirm] = []


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
        address = await addresses.account_address(session, settings)
        owner = await accounts.is_owner(session)
        pending = list(
            await session.scalars(
                select(Search)
                .where(Search.confirm_url.is_not(None), Search.confirmed_at.is_(None))
                .order_by(Search.received_at.desc())
                .limit(10)
            )
        )
        # Démo : les recherches fictives sont déjà là, rien ne s'écrit (docs/76 §1).
        if not settings.demo:
            await service.propose(session)
            await session.flush()
        sites = list(await session.scalars(select(Site).where(followed()).order_by(Site.id)))
        searches = list(
            await session.scalars(
                select(AlertSearch).order_by(AlertSearch.active.desc(), AlertSearch.id)
            )
        )
        rows = [(s, await service.cells(session, s, sites)) for s in searches]
        accepts_remote = (await load_criteria(session)).remote_policy is not RemotePolicy.REFUSE
    by_slug = {s.slug: s for s in sites}

    def cell(search: AlertSearch, found: service.Cell) -> AlertCell:
        remote = (
            service.remote_search_url(by_slug[found.site], search.terms)
            if accepts_remote and found.site in by_slug
            else None
        )
        return AlertCell(**found.__dict__, remote_url=remote)

    return AlertsPage(
        mailbox=address,
        folder=settings.imap_folder if address and owner else None,
        personal_address=bool(address) and not owner,
        to_confirm=[
            ToConfirm(
                search_id=p.id,
                site=p.source,
                subject=p.subject,
                received_at=p.received_at,
                url=p.confirm_url or "",
            )
            for p in pending
        ],
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
                cells=[cell(s, c) for c in found],
            )
            for s, found in rows
        ],
    )


@router.post(
    "/confirmations/{search_id}",
    operation_id="markAlertConfirmed",
    responses={404: {"description": "E-mail introuvable"}},
)
async def mark_confirmed(request: Request, search_id: int) -> AlertsPage:
    """La personne a ouvert le lien de confirmation : il quitte la liste."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        search = await session.get(Search, search_id)
        if search is None or search.confirm_url is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "e-mail introuvable")
        search.confirmed_at = datetime.now(UTC)
    return await _page(runtime)


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


class FirstOffersOut(BaseModel):
    # Rien encore, en file, faite, sans résultat, ou impossible faute de métier.
    status: Literal["none", "queued", "done", "failed", "no_trade"]
    at: datetime | None = None
    found: int = 0
    new: int = 0
    queries: list[str] = []


class FirstOffersStart(FirstOffersOut):
    result: Literal["queued", "already_queued", "no_trade", "too_soon"]


def _first_out(value: dict[str, object]) -> FirstOffersOut:
    found, new, queries, at = (value.get(k) for k in ("found", "new", "queries", "at"))
    raw = value.get("status")
    return FirstOffersOut(
        status=raw if raw in ("queued", "done", "failed", "no_trade") else "none",
        at=datetime.fromisoformat(at) if isinstance(at, str) else None,
        found=found if isinstance(found, int) else 0,
        new=new if isinstance(new, int) else 0,
        queries=[q for q in queries if isinstance(q, str)] if isinstance(queries, list) else [],
    )


@router.get("/first-offers", operation_id="getFirstOffers")
async def get_first_offers(request: Request) -> FirstOffersOut:
    """Les premières offres (docs/104, 0.80.0) : la recherche publique de jobup.

    Rattrapage (0.80.1) : un invité qui a fini son accueil avant la 0.80.0 ne l'a jamais eue ;
    elle part à sa première visite de la page Offres ou Alertes, une seule fois.
    """
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        current = await public_search.state(session)
        missed = (
            not current
            and not runtime.settings.demo
            and not await accounts.is_owner(session)
            and welcome.status(await welcome.state(session)) == "done"
        )
    if missed:
        await public_search.request(runtime, first_only=True)
        async with runtime.sessionmaker() as session:
            current = await public_search.state(session)
    return _first_out(current)


@router.post("/first-offers", operation_id="startFirstOffers", status_code=status.HTTP_202_ACCEPTED)
async def start_first_offers(request: Request) -> FirstOffersStart:
    """« Chercher sur jobup maintenant » : relance la recherche publique (une fois par heure)."""
    runtime = _runtime(request)
    result = await public_search.request(runtime)
    async with runtime.sessionmaker() as session:
        current = _first_out(await public_search.state(session))
    return FirstOffersStart(**current.model_dump(), result=result)
