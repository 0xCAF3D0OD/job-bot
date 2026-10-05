"""Journal des recherches, offres collectées et lancement manuel de la collecte."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import ColumnElement, func, or_, select

from jobbot.core.normalize import normalize_text
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
from jobbot.llm.scoring import profile_hash
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.scoring.service import active_profile
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
    # Note et résumé de l'IA (docs/06), absents tant que l'offre n'est pas notée.
    score: int | None = None
    summary_role: str | None = None
    summary_asks: str | None = None
    summary_offers: str | None = None
    summary_partial: bool = False
    strengths: list["ScorePoint"] = []
    gaps: list["ScorePoint"] = []
    scored_at: datetime | None = None
    # Note faite avec un autre profil que l'actuel : à renoter.
    score_stale: bool = False
    score_error: str | None = None


class ScorePoint(BaseModel):
    text: str
    chunk_ids: list[int]


class OfferCounts(BaseModel):
    to_review: int
    filtered_out: int
    later: int
    # En préparation ou candidature envoyée.
    in_progress: int
    all: int


class OfferPage(BaseModel):
    items: list[OfferOut]
    total: int
    counts: OfferCounts
    facets: "OfferFacets"


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


async def _evaluations(runtime: Runtime, offer_ids: list[int]) -> dict[int, Evaluation]:
    if not offer_ids:
        return {}
    async with runtime.sessionmaker() as session:
        rows = await session.scalars(select(Evaluation).where(Evaluation.offer_id.in_(offer_ids)))
        return {evaluation.offer_id: evaluation for evaluation in rows}


def _evaluation_fields(
    evaluation: Evaluation | None, current_hash: str | None
) -> dict[str, object]:
    if evaluation is None:
        return {}
    fields: dict[str, object] = {
        "filter_reasons": [r["message"] for r in evaluation.filter_reasons],
        "score_error": evaluation.score_error,
    }
    if evaluation.scored_at is not None:
        fields |= {
            "score": evaluation.score,
            "summary_role": evaluation.summary_role,
            "summary_asks": evaluation.summary_asks,
            "summary_offers": evaluation.summary_offers,
            "summary_partial": evaluation.summary_partial,
            "strengths": evaluation.strengths,
            "gaps": evaluation.gaps,
            "scored_at": evaluation.scored_at,
            "score_stale": current_hash is not None and evaluation.profile_hash != current_hash,
        }
    return fields


def _offer_out(
    offer: Offer,
    links: list[OfferLinkOut],
    evaluation: Evaluation | None = None,
    current_hash: str | None = None,
) -> OfferOut:
    return OfferOut.model_validate(
        {**_columns(offer), "links": links, **_evaluation_fields(evaluation, current_hash)}
    )


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


class Facet(BaseModel):
    value: str
    count: int


class OfferFacets(BaseModel):
    """Valeurs disponibles pour les filtres, avec le nombre d'offres de chacune."""

    sources: list[Facet]
    cantons: list[Facet]


# Accents retirés côté base, sans extension PostgreSQL (unaccent n'est pas toujours installé).
_ACCENTED = "àâäáãåéèêëíìîïóòôöõúùûüçñÿ"
_PLAIN = "aaaaaaeeeeiiiiooooouuuucny"


def _searchable() -> ColumnElement[str]:
    text = func.concat_ws(
        " ",
        Offer.title,
        Offer.company,
        Offer.location,
        Offer.snippet,
        Offer.employment_type,
        Offer.description,
    )
    return func.translate(func.lower(text), _ACCENTED, _PLAIN)


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _filters(
    q: str | None,
    sources: list[Source],
    cantons: list[str],
    min_rate: int | None,
    external_only: bool,
) -> list[ColumnElement[bool]]:
    """Filtres d'affichage : ils changent ce que l'on voit, n'écartent rien (docs/06 §7)."""
    conditions: list[ColumnElement[bool]] = []
    if q:
        searchable = _searchable()
        for term in normalize_text(q).split()[:8]:
            conditions.append(searchable.like(f"%{_escape_like(term)}%", escape="\\"))
    if sources:
        conditions.append(
            Offer.id.in_(select(OfferLink.offer_id).where(OfferLink.source.in_(sources)))
        )
    if cantons:
        conditions.append(Offer.canton.in_([c.upper() for c in cantons]))
    if min_rate is not None:
        # Une offre sans taux connu reste visible.
        conditions.append(or_(Offer.rate_max.is_(None), Offer.rate_max >= min_rate))
    if external_only:
        conditions.append(Offer.apply_kind == "external")
    return conditions


IN_PROGRESS = (OfferStatus.PREPARING, OfferStatus.APPLIED)


def _view_condition(view: str) -> ColumnElement[bool] | None:
    if view == "to_review":
        return Offer.status.in_(TO_REVIEW)
    if view == "filtered_out":
        return Offer.status == OfferStatus.FILTERED_OUT
    if view == "later":
        return Offer.status == OfferStatus.LATER
    if view == "in_progress":
        return Offer.status.in_(IN_PROGRESS)
    return None


@router.get("/offers", operation_id="listOffers")
async def list_offers(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort: Literal["recent", "popular", "score"] = "recent",
    view: Literal["to_review", "filtered_out", "later", "in_progress", "all"] = "all",
    q: Annotated[str | None, Query(max_length=200)] = None,
    min_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    sources: Annotated[list[Source], Query()] = [],  # noqa: B006
    cantons: Annotated[list[str], Query(max_length=26)] = [],  # noqa: B006
    min_rate: Annotated[int | None, Query(ge=1, le=100)] = None,
    external_only: bool = False,
) -> OfferPage:
    """`recent` : dernières offres apparues ; `popular` : offres vues dans le plus d'alertes ;
    `score` : meilleure note de l'IA d'abord (offres non notées à la fin).
    `view` : à examiner, écartées par le filtre, ou toutes. Les autres paramètres sont des
    filtres d'affichage ; les compteurs par statut et les facettes en tiennent compte."""
    runtime = _runtime(request)
    score = (
        select(Evaluation.score)
        .where(Evaluation.offer_id == Offer.id, Evaluation.scored_at.is_not(None))
        .scalar_subquery()
    )
    order = {
        "popular": (Offer.seen_count.desc(), Offer.last_seen_at.desc(), Offer.id.desc()),
        "score": (score.desc().nulls_last(), Offer.first_seen_at.desc(), Offer.id.desc()),
    }.get(sort, (Offer.first_seen_at.desc(), Offer.id.desc()))
    conditions = _filters(q, sources, cantons, min_rate, external_only)
    if min_score is not None:
        conditions.append(score >= min_score)
    view_condition = _view_condition(view)
    listed = [*conditions, *([view_condition] if view_condition is not None else [])]
    # Facettes : calculées sans le filtre qu'elles décrivent, pour pouvoir élargir le choix.
    without_sources = _filters(q, [], cantons, min_rate, external_only)
    without_cantons = _filters(q, sources, [], min_rate, external_only)
    if min_score is not None:
        without_sources.append(score >= min_score)
        without_cantons.append(score >= min_score)
    if view_condition is not None:
        without_sources.append(view_condition)
        without_cantons.append(view_condition)

    async with runtime.sessionmaker() as session:
        by_status = dict(
            (
                await session.execute(
                    select(Offer.status, func.count()).where(*conditions).group_by(Offer.status)
                )
            ).all()
        )
        offers = list(
            await session.scalars(
                select(Offer).where(*listed).order_by(*order).limit(limit).offset(offset)
            )
        )
        source_rows = (
            await session.execute(
                select(OfferLink.source, func.count(func.distinct(OfferLink.offer_id)))
                .join(Offer, Offer.id == OfferLink.offer_id)
                .where(*without_sources)
                .group_by(OfferLink.source)
            )
        ).all()
        canton_rows = (
            await session.execute(
                select(Offer.canton, func.count())
                .where(Offer.canton.is_not(None), *without_cantons)
                .group_by(Offer.canton)
            )
        ).all()

    counts = OfferCounts(
        to_review=sum(by_status.get(s, 0) for s in TO_REVIEW),
        filtered_out=by_status.get(OfferStatus.FILTERED_OUT, 0),
        later=by_status.get(OfferStatus.LATER, 0),
        in_progress=sum(by_status.get(s, 0) for s in IN_PROGRESS),
        all=sum(by_status.values()),
    )
    total = counts.model_dump().get(view, counts.all)
    facets = OfferFacets(
        sources=[Facet(value=str(v), count=c) for v, c in sorted(source_rows)],
        cantons=[
            Facet(value=str(v), count=c)
            for v, c in sorted(canton_rows, key=lambda row: (-row[1], row[0]))
        ],
    )
    ids = [offer.id for offer in offers]
    links, evaluations = await _links(runtime, ids), await _evaluations(runtime, ids)
    async with runtime.sessionmaker() as session:
        current_hash = profile_hash(await active_profile(session))
    return OfferPage(
        items=[_offer_out(o, links[o.id], evaluations.get(o.id), current_hash) for o in offers],
        total=total,
        counts=counts,
        facets=facets,
    )


@router.get("/offers/{offer_id}", operation_id="getOffer")
async def get_offer(request: Request, offer_id: int) -> OfferOut:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        offer = await session.get(Offer, offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        current_hash = profile_hash(await active_profile(session))
    links, evaluations = await _links(runtime, [offer_id]), await _evaluations(runtime, [offer_id])
    return _offer_out(offer, links[offer_id], evaluations.get(offer_id), current_hash)


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
