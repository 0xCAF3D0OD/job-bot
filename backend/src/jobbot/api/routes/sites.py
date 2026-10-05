"""Sites suivis : liste, ajout, pause, suppression, relecture des alertes (docs/11 §2)."""

import re
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select

from jobbot.collect.service import reparse
from jobbot.core.normalize import normalize_text
from jobbot.db.models import ParseStatus, Search, Site, SiteReader
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api", tags=["sites"])
_SENDER = re.compile(r"^([a-z0-9._%+-]+@)?[a-z0-9-]+(\.[a-z0-9-]+)+$")


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class SiteOut(BaseModel):
    id: int
    slug: str
    name: str
    senders: list[str]
    url: str | None
    reader: Literal["jobup", "indeed", "ai"]
    active: bool
    builtin: bool
    alerts: int
    last_alert_at: datetime | None
    # Alertes non reconnues reçues de ce site, que « Relire » peut traiter.
    unrecognized: int


class SiteIn(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=60)]
    senders: list[Annotated[str, Field(max_length=120)]] = Field(min_length=1, max_length=10)
    url: Annotated[str, Field(max_length=300)] | None = None

    @field_validator("senders")
    @classmethod
    def _senders(cls, values: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(v.strip().lower() for v in values if v.strip()))
        for value in cleaned:
            if not _SENDER.match(value):
                raise ValueError(f"adresse ou domaine invalide : {value}")
        if not cleaned:
            raise ValueError("au moins une adresse d'expédition")
        return cleaned

    @field_validator("url")
    @classmethod
    def _url(cls, value: str | None) -> str | None:
        value = (value or "").strip()
        if value and not value.startswith("https://"):
            raise ValueError("adresse du site en https://")
        return value or None


class SiteActive(BaseModel):
    active: bool


class RereadOut(BaseModel):
    examined: int
    updated: int
    new_offers: int


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", normalize_text(name))[:30]


async def _list(runtime: Runtime) -> list[SiteOut]:
    async with runtime.sessionmaker() as session:
        sites = list(await session.scalars(select(Site).order_by(Site.builtin.desc(), Site.id)))
        stats = {
            source: (count, last)
            for source, count, last in (
                await session.execute(
                    select(Search.source, func.count(), func.max(Search.received_at)).group_by(
                        Search.source
                    )
                )
            ).all()
        }
        unrecognized = dict(
            (
                await session.execute(
                    select(Search.source, func.count())
                    .where(Search.parse_status == ParseStatus.UNRECOGNIZED)
                    .group_by(Search.source)
                )
            ).all()
        )
    return [
        SiteOut(
            id=s.id,
            slug=s.slug,
            name=s.name,
            senders=list(s.senders),
            url=s.url,
            reader=s.reader,
            active=s.active,
            builtin=s.builtin,
            alerts=stats.get(s.slug, (0, None))[0],
            last_alert_at=stats.get(s.slug, (0, None))[1],
            unrecognized=unrecognized.get(s.slug, 0),
        )
        for s in sites
    ]


@router.get("/sites", operation_id="listSites")
async def list_sites(request: Request) -> list[SiteOut]:
    return await _list(_runtime(request))


@router.post("/sites", operation_id="addSite", status_code=status.HTTP_201_CREATED)
async def add_site(request: Request, body: SiteIn) -> list[SiteOut]:
    """Nouveau site : ses alertes seront lues par l'IA."""
    runtime = _runtime(request)
    slug = _slug(body.name)
    if len(slug) < 2:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "nom de site trop court")
    async with runtime.sessionmaker.begin() as session:
        if await session.scalar(select(Site.id).where(Site.slug == slug)):
            raise HTTPException(status.HTTP_409_CONFLICT, "ce site est déjà suivi")
        session.add(
            Site(
                slug=slug,
                name=body.name.strip(),
                senders=body.senders,
                url=body.url,
                reader=SiteReader.AI,
                active=True,
            )
        )
    return await _list(runtime)


@router.patch("/sites/{site_id}", operation_id="setSiteActive")
async def set_site_active(request: Request, site_id: int, body: SiteActive) -> list[SiteOut]:
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        site = await session.get(Site, site_id)
        if site is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "site introuvable")
        site.active = body.active
    return await _list(runtime)


@router.delete("/sites/{site_id}", operation_id="deleteSite")
async def delete_site(request: Request, site_id: int) -> list[SiteOut]:
    """Retire un site ajouté ; ses offres déjà collectées restent."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        site = await session.get(Site, site_id)
        if site is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "site introuvable")
        if site.builtin:
            raise HTTPException(status.HTTP_409_CONFLICT, "site intégré : le mettre en pause")
        await session.delete(site)
    return await _list(runtime)


@router.post("/sites/reread", operation_id="rereadUnrecognized")
async def reread_unrecognized(request: Request) -> RereadOut:
    """Relit les alertes non reconnues (par exemple celles d'un site qu'on vient d'ajouter)."""
    result = await reparse(_runtime(request), parse_status=ParseStatus.UNRECOGNIZED)
    return RereadOut(examined=result.examined, updated=result.updated, new_offers=result.new_offers)
