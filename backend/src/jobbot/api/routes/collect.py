"""Journal des recherches, offres collectées et lancement manuel de la collecte."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select

from jobbot.db.models import (
    Evaluation,
    Offer,
    OfferLink,
    OfferSighting,
    OfferStatus,
    ParseStatus,
    Search,
    Source,
)
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.worker.queue import enqueue
from jobbot.worker.tasks.collect import COLLECT_JOB

router = APIRouter(prefix="/api", tags=["collect"])
log = get_logger(__name__)


class SearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: Source
    received_at: datetime
    subject: str | None
    alert_label: str | None
    parse_status: ParseStatus
    parser_version: str | None
    error: str | None
    results_count: int
    new_offers_count: int
    collected_at: datetime


class SearchPage(BaseModel):
    items: list[SearchOut]
    total: int


class OfferLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source: Source
    url: str


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str | None
    location: str | None
    rate_min: int | None
    rate_max: int | None
    snippet: str | None
    status: OfferStatus
    first_seen_at: datetime
    last_seen_at: datetime
    seen_count: int
    links: list[OfferLinkOut]
    # Lien de candidature et texte complet, lus sur la page de l'offre (jobup seulement).
    apply_url: str | None = None
    apply_kind: Literal["external", "jobup"] | None = None
    description: str | None = None
    employment_type: str | None = None
    enrich_status: Literal["pending", "ok", "expired", "failed", "skipped"] = "pending"
    # Raisons d'exclusion données par le filtre (vide si l'offre passe ou n'est pas filtrée).
    filter_reasons: list[str] = []


class OfferCounts(BaseModel):
    to_review: int
    filtered_out: int
    all: int


class OfferPage(BaseModel):
    items: list[OfferOut]
    total: int
    counts: OfferCounts


class SearchOffer(OfferOut):
    # Vrai si l'offre est apparue pour la première fois dans cette alerte.
    is_first: bool


class SearchDetail(SearchOut):
    offers: list[SearchOffer]


class CollectResponse(BaseModel):
    result: Literal["queued", "already_queued"]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


async def _links(runtime: Runtime, offer_ids: list[int]) -> dict[int, list[OfferLinkOut]]:
    links: dict[int, list[OfferLinkOut]] = {i: [] for i in offer_ids}
    if not offer_ids:
        return links
    async with runtime.sessionmaker() as session:
        rows = await session.scalars(
            select(OfferLink).where(OfferLink.offer_id.in_(offer_ids)).order_by(OfferLink.id)
        )
        for link in rows:
            links[link.offer_id].append(OfferLinkOut.model_validate(link))
    return links


async def _reasons(runtime: Runtime, offer_ids: list[int]) -> dict[int, list[str]]:
    reasons: dict[int, list[str]] = {i: [] for i in offer_ids}
    if not offer_ids:
        return reasons
    async with runtime.sessionmaker() as session:
        rows = await session.scalars(select(Evaluation).where(Evaluation.offer_id.in_(offer_ids)))
        for evaluation in rows:
            reasons[evaluation.offer_id] = [r["message"] for r in evaluation.filter_reasons]
    return reasons


def _offer_out(offer: Offer, links: list[OfferLinkOut], reasons: list[str]) -> OfferOut:
    return OfferOut.model_validate({**_columns(offer), "links": links, "filter_reasons": reasons})


# « À examiner » regroupe les offres retenues par le filtre et celles qui n'y sont pas encore
# passées : une offre n'est jamais cachée faute d'avoir été filtrée.
TO_REVIEW = (OfferStatus.NEW, OfferStatus.TO_REVIEW)


def _columns(offer: Offer) -> dict[str, object]:
    return {c.key: getattr(offer, c.key) for c in Offer.__table__.columns}


@router.get("/searches", operation_id="listSearches")
async def list_searches(
    request: Request,
    source: Source | None = None,
    parse_status: ParseStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SearchPage:
    runtime = _runtime(request)
    query = select(Search)
    if source is not None:
        query = query.where(Search.source == source)
    if parse_status is not None:
        query = query.where(Search.parse_status == parse_status)
    async with runtime.sessionmaker() as session:
        total = await session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await session.scalars(
            query.order_by(Search.received_at.desc(), Search.id.desc()).limit(limit).offset(offset)
        )
        items = [SearchOut.model_validate(row) for row in rows]
    return SearchPage(items=items, total=total or 0)


@router.get("/searches/{search_id}", operation_id="getSearch")
async def get_search(request: Request, search_id: int) -> SearchDetail:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        search = await session.get(Search, search_id)
        if search is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "alerte introuvable")
        rows = (
            await session.execute(
                select(Offer, OfferSighting.is_first)
                .join(OfferSighting, OfferSighting.offer_id == Offer.id)
                .where(OfferSighting.search_id == search_id)
                .order_by(OfferSighting.position)
            )
        ).all()
    links = await _links(runtime, [offer.id for offer, _ in rows])
    offers = [
        SearchOffer.model_validate({**_columns(offer), "links": links[offer.id], "is_first": first})
        for offer, first in rows
    ]
    return SearchDetail.model_validate(
        {**SearchOut.model_validate(search).model_dump(), "offers": offers}
    )


@router.get("/offers", operation_id="listOffers")
async def list_offers(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort: Literal["recent", "popular"] = "recent",
    view: Literal["to_review", "filtered_out", "all"] = "all",
) -> OfferPage:
    """`recent` : dernières offres apparues ; `popular` : offres vues dans le plus d'alertes.
    `view` : à examiner, écartées par le filtre, ou toutes."""
    runtime = _runtime(request)
    order = (
        (Offer.seen_count.desc(), Offer.last_seen_at.desc(), Offer.id.desc())
        if sort == "popular"
        else (Offer.first_seen_at.desc(), Offer.id.desc())
    )
    query = select(Offer)
    if view == "to_review":
        query = query.where(Offer.status.in_(TO_REVIEW))
    elif view == "filtered_out":
        query = query.where(Offer.status == OfferStatus.FILTERED_OUT)
    async with runtime.sessionmaker() as session:
        by_status = dict(
            (await session.execute(select(Offer.status, func.count()).group_by(Offer.status))).all()
        )
        offers = list(await session.scalars(query.order_by(*order).limit(limit).offset(offset)))
    counts = OfferCounts(
        to_review=sum(by_status.get(s, 0) for s in TO_REVIEW),
        filtered_out=by_status.get(OfferStatus.FILTERED_OUT, 0),
        all=sum(by_status.values()),
    )
    total = {"to_review": counts.to_review, "filtered_out": counts.filtered_out}.get(
        view, counts.all
    )
    ids = [offer.id for offer in offers]
    links, reasons = await _links(runtime, ids), await _reasons(runtime, ids)
    return OfferPage(
        items=[_offer_out(o, links[o.id], reasons[o.id]) for o in offers],
        total=total,
        counts=counts,
    )


@router.post(
    "/collect",
    operation_id="startCollect",
    status_code=status.HTTP_202_ACCEPTED,
    responses={409: {"description": "Collecte non configurée"}},
)
async def start_collect(request: Request) -> CollectResponse:
    runtime = _runtime(request)
    if not runtime.settings.imap_configured:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Collecte non configurée : renseigner JOBBOT_IMAP_USER et JOBBOT_IMAP_PASSWORD.",
        )
    queued = await enqueue(runtime.settings, COLLECT_JOB)
    log.info("collect_requested", queued=queued)
    return CollectResponse(result="queued" if queued else "already_queued")
