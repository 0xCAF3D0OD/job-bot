"""Journal des recherches, offres collectées et lancement manuel de la collecte."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import ColumnElement, Time, and_, case, cast, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.filter import Criteria, Language, languages_to_check, remote_location
from jobbot.core.normalize import normalize_text
from jobbot.core.orp import LOCAL_TZ
from jobbot.db.models import (
    IGNORED_KIND,
    Application,
    CompanyLogo,
    Draft,
    Evaluation,
    Offer,
    OfferLink,
    OfferSighting,
    OfferStatus,
    ParseStatus,
    Search,
)
from jobbot.employer import service as employer_service
from jobbot.filtering.service import load_criteria
from jobbot.llm.scoring import PART_MAX, profile_hash
from jobbot.log import get_logger
from jobbot.registry.service import name_key
from jobbot.runtime import Runtime
from jobbot.scoring.service import active_profile
from jobbot.worker.queue import enqueue
from jobbot.worker.tasks.collect import COLLECT_JOB

# Identifiant d'un site suivi (jobup, indeed, jobsch, linkedin…).
SiteSlug = Annotated[str, Field(pattern=r"^[a-z0-9]{2,30}$")]

router = APIRouter(prefix="/api", tags=["collect"])
log = get_logger(__name__)


class SearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # Identifiant du site (jobup, indeed, jobsch, linkedin…), voir /api/sites.
    source: str
    received_at: datetime
    subject: str | None
    alert_label: str | None
    parse_status: ParseStatus
    parser_version: str | None
    error: str | None
    results_count: int
    new_offers_count: int
    # Recommandations du site écartées, hors métier (docs/116 §3).
    off_topic_count: int = 0
    collected_at: datetime


class SearchPage(BaseModel):
    items: list[SearchOut]
    total: int


class OfferLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Identifiant du site (jobup, indeed, jobsch, linkedin…), voir /api/sites.
    source: str
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
    # Offre retirée : page introuvable, ou plus vue dans les alertes depuis 30 jours.
    expired_at: datetime | None = None
    expiry_source: Literal["page", "age", "manual"] | None = None
    # Choix de Kevin, prioritaire sur la détection automatique.
    expiry_override: Literal["expired", "alive"] | None = None
    # Adresse de l'entreprise (docs/12 §2) et sa source.
    company_address: str | None = None
    company_address_source: Literal["page", "registry", "web", "letter", "manual"] | None = None
    company_address_url: str | None = None
    # Annonce chez l'employeur (docs/20 §2) : adresse vérifiée et sa source
    # (site, outil de recrutement, Internet) ; résultat de la recherche.
    employer_url: str | None = None
    employer_url_source: Literal["site", "ats", "web"] | None = None
    employer_status: Literal["found", "not_found", "agency", "gone"] | None = None
    employer_checked_at: datetime | None = None
    # Logo de l'entreprise disponible sur /api/offers/{id}/logo (docs/14 §4).
    has_logo: bool = False
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
    # Pourquoi cette note, et le niveau visé (score-v5, docs/121 §C) ; vides avant.
    why: str | None = None
    level: Literal["above", "below"] | None = None
    level_detail: str | None = None
    # Comment la note est calculée (score-v7, PR 18) : vide pour une note plus ancienne.
    score_parts: list["ScorePartOut"] = []
    score_tip: "ScoreTipOut | None" = None
    scored_at: datetime | None = None
    # Note faite avec un autre profil que l'actuel : à renoter.
    score_stale: bool = False
    score_error: str | None = None
    # « Note impossible », état final (A2 du 13 novembre) : rien à lire, réponse vide de l'IA ou
    # erreur après 3 essais. Absent tant que la note peut encore arriver.
    score_final: Literal["sans_texte", "reponse_vide", "erreur"] | None = None
    # Étiquettes des cartes (docs/11 §3), vides pour une note antérieure à score-v2.
    keywords_role: list[str] = []
    keywords_asks: list["AskKeywordOut"] = []
    keywords_offers: list[str] = []
    # Télétravail (docs/26 §2) : relevé par l'IA à la notation, ou annoncé par le lieu.
    remote: Literal["onsite", "hybrid", "full", "unknown"] | None = None
    remote_days: int | None = None
    remote_region: str | None = None
    remote_from_switzerland: bool | None = None
    # Signaux « à vérifier » (docs/30 §2) : annonce permanente, employeur caché, arnaque possible.
    doubts: list["DoubtOut"] = []
    # Candidature spontanée, créée par toi sans annonce (docs/39).
    spontaneous: bool = False
    # Offre ajoutée par toi, par son lien ou son texte (docs/111).
    added_by_you: bool = False
    # Lecture automatique de l'annonce complète (prompt du 10 novembre, PR 13) : « reading »
    # tant qu'elle est à faire ou en cours, « done » quand jobA1 l'a lue (ou qu'elle a été
    # collée) et la note refaite, « refused » si le site bloque la lecture ; None : l'offre avait
    # son texte complet dès le départ, ou c'est une candidature spontanée.
    text_reading: Literal["reading", "done", "refused"] | None = None
    # Langues exigées par l'annonce dont tu n'as pas renseigné le niveau (PR 17) : « Langue à
    # vérifier » dans le détail.
    languages_to_check: list[Language] = []


class DoubtOut(BaseModel):
    kind: Literal["permanent", "hidden_employer", "scam"]
    text: str
    excerpt: str | None = None


class AskKeywordOut(BaseModel):
    text: str
    covered: bool | None = None


class ScorePoint(BaseModel):
    text: str
    chunk_ids: list[int]


class ScorePartOut(BaseModel):
    """Une part de la note (PR 18) : `max` vient de PART_MAX, `points` de la notation."""

    key: Literal["skills", "experience", "location", "languages", "terms"]
    points: int
    max: int
    text: str
    check: bool = False


class ScoreTipOut(BaseModel):
    text: str
    action: Literal["skills", "experience", "languages", "criteria"] | None = None


class OfferCounts(BaseModel):
    to_review: int
    # À traiter, sans les filtres de la liste : le nombre de la pastille (count_pending).
    pending: int
    filtered_out: int
    later: int
    # En préparation ou candidature envoyée (expirées comprises : un bandeau le signale).
    in_progress: int
    # Retirées par l'employeur ; exclues des autres compteurs.
    expired: int
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
    """Liens de chaque offre, avec ceux de ses doublons (docs/30 §3), sans répétition."""
    links: dict[int, list[OfferLinkOut]] = {i: [] for i in offer_ids}
    if not offer_ids:
        return links
    async with runtime.sessionmaker() as session:
        rows = await session.execute(
            select(OfferLink, func.coalesce(Offer.duplicate_of, Offer.id))
            .join(Offer, Offer.id == OfferLink.offer_id)
            .where(or_(Offer.id.in_(offer_ids), Offer.duplicate_of.in_(offer_ids)))
            .order_by(OfferLink.id)
        )
        for link, owner in rows:
            target = owner if owner in links else link.offer_id
            out = OfferLinkOut.model_validate(link)
            if target in links and all(
                (x.source, x.url) != (out.source, out.url) for x in links[target]
            ):
                links[target].append(out)
    return links


PERMANENT_AFTER = timedelta(days=30)


def _doubts(offer: Offer, evaluation: Evaluation | None) -> list["DoubtOut"]:
    """Signaux « à vérifier » (docs/30 §2) ; rien n'est écarté pour autant."""
    found: list[DoubtOut] = []
    if offer.spontaneous:
        return found
    since = offer.seen_since or offer.first_seen_at
    age = datetime.now(UTC) - since
    if offer.expired_at is None and age > PERMANENT_AFTER:
        found.append(
            DoubtOut(
                kind="permanent",
                text=f"Annonce permanente : vue dans les alertes depuis {age.days} jours.",
            )
        )
    if not (offer.company or "").strip():
        found.append(
            DoubtOut(kind="hidden_employer", text="Employeur caché : aucune entreprise indiquée.")
        )
    elif offer.employer_status == "agency":
        found.append(
            DoubtOut(
                kind="hidden_employer",
                text="Employeur caché : annonce d'agence, employeur non nommé.",
            )
        )
    for signal in (evaluation.scam_signals if evaluation else None) or []:
        found.append(
            DoubtOut(
                kind="scam",
                text=f"Arnaque possible : {signal.get('reason', '')}",
                excerpt=signal.get("excerpt") or None,
            )
        )
    return found


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
        "score_final": evaluation.score_final
        if evaluation.score_final in ("sans_texte", "reponse_vide", "erreur")
        else None,
    }
    if evaluation.scored_at is not None:
        fields |= {
            "score": evaluation.score,
            "summary_role": evaluation.summary_role,
            "summary_asks": evaluation.summary_asks,
            "summary_offers": evaluation.summary_offers,
            "summary_partial": evaluation.summary_partial,
            "keywords_role": evaluation.keywords_role or [],
            "keywords_asks": evaluation.keywords_asks or [],
            "keywords_offers": evaluation.keywords_offers or [],
            "strengths": evaluation.strengths,
            "gaps": evaluation.gaps,
            "why": evaluation.why,
            "level": evaluation.level if evaluation.level in ("above", "below") else None,
            "level_detail": evaluation.level_detail,
            "score_parts": [
                {**part, "max": PART_MAX[part["key"]]}
                for part in evaluation.score_parts or []
                if part.get("key") in PART_MAX
            ],
            "score_tip": evaluation.score_tip,
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
    remote: dict[str, object] = {}
    if evaluation is not None and evaluation.remote:
        remote = {
            "remote": evaluation.remote,
            "remote_days": evaluation.remote_days,
            "remote_region": evaluation.remote_region,
            "remote_from_switzerland": evaluation.remote_from_switzerland,
        }
    elif remote_location(offer.location):
        remote = {"remote": "full"}
    return OfferOut.model_validate(
        {
            **_columns(offer),
            # Une offre ajoutée par son texte n'a pas de lien : rien à ouvrir.
            "links": [link for link in links if link.url],
            "added_by_you": any(link.source == "manual" for link in links),
            **_evaluation_fields(evaluation, current_hash),
            **remote,
            "doubts": _doubts(offer, evaluation),
            "text_reading": text_reading(offer),
        }
    )


def text_reading(offer: Offer) -> str | None:
    """L'état de la lecture automatique de l'annonce complète, pour la carte de la note."""
    if offer.spontaneous:
        return None
    if offer.description:
        return "done" if offer.text_read == "done" else None
    return "refused" if offer.text_read == "refused" else "reading"


# « À examiner » regroupe les offres retenues par le filtre et celles qui n'y sont pas encore
# passées : une offre n'est jamais cachée faute d'avoir été filtrée.
TO_REVIEW = (OfferStatus.NEW, OfferStatus.TO_REVIEW)


def _columns(offer: Offer) -> dict[str, object]:
    return {c.key: getattr(offer, c.key) for c in Offer.__table__.columns}


@router.get("/searches", operation_id="listSearches")
async def list_searches(
    request: Request,
    source: Annotated[str | None, Query(max_length=30)] = None,
    parse_status: ParseStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SearchPage:
    runtime = _runtime(request)
    # Un e-mail qui ne vient d'aucun site n'est pas une alerte : rien à montrer.
    query = select(Search).where(Search.kind.is_distinct_from(IGNORED_KIND))
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
    # Courbe des notes (docs/27 §3) : nombre d'offres notées par tranche de 5 points
    # (0-4, 5-9… 95-100), sans le filtre de note lui-même ; et les offres pas encore notées.
    scores: list[int] = []
    unscored: int = 0
    # Filtre « Note » : offres notées sur l'annonce complète (sûres) ou sur l'extrait de l'alerte
    # seulement (provisoires), sans ce filtre lui-même.
    sure: int = 0
    provisional: int = 0


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


def _doubtful() -> ColumnElement[bool]:
    """Les mêmes signaux que `_doubts`, en SQL, pour « Masquer les offres à vérifier »."""
    scam = Offer.id.in_(
        select(Evaluation.offer_id).where(func.jsonb_array_length(Evaluation.scam_signals) > 0)
    )
    permanent = and_(
        Offer.expired_at.is_(None),
        func.coalesce(Offer.seen_since, Offer.first_seen_at) < func.now() - PERMANENT_AFTER,
    )
    hidden = or_(
        Offer.company.is_(None),
        func.btrim(Offer.company) == "",
        # Valeur vide : ni vrai ni faux en SQL ; ramenée à « pas une agence ».
        func.coalesce(Offer.employer_status, "") == "agency",
    )
    return and_(Offer.spontaneous.is_(False), or_(scam, permanent, hidden))


REMOTE_WORDS = ("remote", "home office", "homeoffice", "teletravail", "télétravail")


def _remote_condition(remote: str | None) -> ColumnElement[bool] | None:
    """`partial` : au moins partiel (partiel ou complet) ; `full` : entièrement à distance.
    Un lieu « Remote » compte comme complet, même avant la notation."""
    if remote is None:
        return None
    wanted = ("hybrid", "full") if remote == "partial" else ("full",)
    by_ai = Offer.id.in_(select(Evaluation.offer_id).where(Evaluation.remote.in_(wanted)))
    by_location = or_(*(Offer.location.ilike(f"%{word}%") for word in REMOTE_WORDS))
    return or_(by_ai, by_location)


def _filters(
    q: str | None,
    sources: list[str],
    cantons: list[str],
    min_rate: int | None,
    external_only: bool,
    remote: str | None = None,
    hide_doubtful: bool = False,
) -> list[ColumnElement[bool]]:
    """Filtres d'affichage : ils changent ce que l'on voit, n'écartent rien (docs/06 §7).
    Un doublon n'apparaît jamais : son offre gardée porte tous ses liens (docs/30 §3)."""
    conditions: list[ColumnElement[bool]] = [Offer.duplicate_of.is_(None)]
    if hide_doubtful:
        conditions.append(_doubtful().is_(False))
    if (remote_filter := _remote_condition(remote)) is not None:
        conditions.append(remote_filter)
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


def _view_condition(
    view: str, with_filtered_out: bool = False, with_expired: bool = False
) -> ColumnElement[bool] | None:
    """Une offre expirée n'apparaît que dans « Expirées », sauf si elle est en cours."""
    live = Offer.expired_at.is_(None)
    if view == "to_review":
        return and_(Offer.status.in_(TO_REVIEW), live)
    if view == "pending":
        # En préparation, elle reste à traiter même retirée : un bandeau le dit dans la fiche.
        # « Masquer les offres écartées » coupé (docs/139, C2) : elles s'y ajoutent.
        shown = (
            *TO_REVIEW,
            OfferStatus.LATER,
            *((OfferStatus.FILTERED_OUT,) if with_filtered_out else ()),
        )
        # « Afficher aussi : Expirées » (docs/139, 5e) : la vue « Expirées » s'y ajoute.
        expired = and_(Offer.expired_at.is_not(None), Offer.status.not_in(IN_PROGRESS))
        return or_(
            and_(Offer.status.in_(shown), live),
            Offer.status == OfferStatus.PREPARING,
            *((expired,) if with_expired else ()),
        )
    if view == "filtered_out":
        return and_(Offer.status == OfferStatus.FILTERED_OUT, live)
    if view == "later":
        return and_(Offer.status == OfferStatus.LATER, live)
    if view == "in_progress":
        return Offer.status.in_(IN_PROGRESS)
    if view == "expired":
        return and_(Offer.expired_at.is_not(None), Offer.status.not_in(IN_PROGRESS))
    return or_(live, Offer.status.in_(IN_PROGRESS))


# Les offres « Loin » (note sous 50) : cachées de la liste sur téléphone tant qu'aucun filtre
# de note n'est posé (maquette Candidatures, Kevin 2026-11-06). Une offre sans note n'est pas
# « Loin ».
FAR_BELOW = 50


async def count_pending(
    session: AsyncSession, conditions: Sequence[ColumnElement[bool]] = (), *, near: bool = False
) -> int:
    """« À traiter » (docs/139, C2) : à examiner, plus tard et en préparation.

    Le seul calcul de ce nombre : la phrase de la liste et la pastille du segment le lisent ici.
    `near` : sans les offres « Loin », comme la liste du téléphone (la pastille de la barre du bas).
    """
    pending = _view_condition("pending")
    query = select(func.count()).select_from(Offer).where(Offer.duplicate_of.is_(None), *conditions)
    if near:
        far = (
            select(Evaluation.id)
            .where(
                Evaluation.offer_id == Offer.id,
                Evaluation.scored_at.is_not(None),
                Evaluation.score < FAR_BELOW,
            )
            .exists()
        )
        query = query.where(~far)
    return int(await session.scalar(query.where(pending) if pending is not None else query) or 0)


@router.get("/offers", operation_id="listOffers")
async def list_offers(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort: Literal["recent", "day", "popular", "score", "activity"] = "recent",
    view: Literal[
        "to_review", "pending", "filtered_out", "later", "in_progress", "expired", "all"
    ] = "all",
    q: Annotated[str | None, Query(max_length=200)] = None,
    min_score: Annotated[int | None, Query(ge=1, le=100)] = None,
    max_score: Annotated[int | None, Query(ge=0, le=99)] = None,
    sources: Annotated[list[SiteSlug], Query(max_length=20)] = [],  # noqa: B006
    cantons: Annotated[list[str], Query(max_length=26)] = [],  # noqa: B006
    min_rate: Annotated[int | None, Query(ge=1, le=100)] = None,
    external_only: bool = False,
    remote: Literal["partial", "full"] | None = None,
    hide_doubtful: bool = False,
    with_filtered_out: bool = False,
    with_expired: bool = False,
    basis: Literal["sure", "provisional"] | None = None,
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
    # Dernière action (docs/14 §3) : date d'envoi de la candidature (avec l'heure de
    # l'enregistrement), sinon dernière lettre ou dernier CV, sinon arrivée de l'offre.
    sent = (
        select(func.max(Application.sent_at + cast(Application.created_at, Time)))
        .where(Application.offer_id == Offer.id)
        .scalar_subquery()
    )
    drafted = (
        select(func.max(func.coalesce(Draft.edited_at, Draft.created_at)))
        .where(Draft.offer_id == Offer.id)
        .scalar_subquery()
    )
    activity = func.coalesce(sent, drafted, Offer.first_seen_at)
    # Jour de réception, heure suisse : les offres d'un même jour, la mieux notée d'abord.
    day = func.date(func.timezone(LOCAL_TZ.key, Offer.first_seen_at))
    order: tuple[ColumnElement[Any], ...] = {
        "day": (day.desc(), score.desc().nulls_last(), Offer.first_seen_at.desc(), Offer.id.desc()),
        "popular": (Offer.seen_count.desc(), Offer.last_seen_at.desc(), Offer.id.desc()),
        "score": (score.desc().nulls_last(), Offer.first_seen_at.desc(), Offer.id.desc()),
        "activity": (activity.desc(), Offer.id.desc()),
    }.get(sort, (Offer.first_seen_at.desc(), Offer.id.desc()))
    if view == "pending":
        # À traiter : les offres en préparation d'abord (docs/139, C2), puis l'ordre du tri.
        first: ColumnElement[Any] = case((Offer.status == OfferStatus.PREPARING, 0), else_=1)
        order = (first, *order)
    conditions = _filters(q, sources, cantons, min_rate, external_only, remote, hide_doubtful)
    # Sans le filtre de note : base de la courbe des notes.
    without_score = [*conditions]
    if min_score is not None:
        conditions.append(score >= min_score)
    if max_score is not None:
        conditions.append(score <= max_score)
    view_condition = _view_condition(view, with_filtered_out, with_expired)
    # « Note » : provisoire = notée sans le texte de l'annonce (la pastille « Provisoire » de la
    # fiche) ; sûre = notée sur l'annonce complète. Les nombres se comptent sans ce filtre.
    provisional = and_(
        score.is_not(None),
        func.coalesce(Offer.description, "") == "",
        Offer.spontaneous.is_(False),
    )
    sure = and_(score.is_not(None), not_(provisional))
    without_basis = [*conditions, *([view_condition] if view_condition is not None else [])]
    if basis is not None:
        conditions.append(provisional if basis == "provisional" else sure)
    listed = [*conditions, *([view_condition] if view_condition is not None else [])]
    # Facettes : calculées sans le filtre qu'elles décrivent, pour pouvoir élargir le choix.
    without_sources = _filters(q, [], cantons, min_rate, external_only, remote, hide_doubtful)
    without_cantons = _filters(q, sources, [], min_rate, external_only, remote, hide_doubtful)
    for bound in (
        *([score >= min_score] if min_score is not None else []),
        *([score <= max_score] if max_score is not None else []),
    ):
        without_sources.append(bound)
        without_cantons.append(bound)
    if basis is not None:
        for others in (without_score, without_sources, without_cantons):
            others.append(provisional if basis == "provisional" else sure)
    if view_condition is not None:
        without_score.append(view_condition)
    if view_condition is not None:
        without_sources.append(view_condition)
        without_cantons.append(view_condition)

    async with runtime.sessionmaker() as session:
        # « À traiter » sans les filtres : le nombre de la pastille, une seule source (docs/139).
        pending = await count_pending(session)
        # Le total décrit ce que la liste montre : la vue et les filtres, rien d'autre.
        total = int(
            await session.scalar(select(func.count()).select_from(Offer).where(*listed)) or 0
        )
        expired_flag = Offer.expired_at.is_not(None)
        grouped = (
            await session.execute(
                select(Offer.status, expired_flag, func.count())
                .where(*conditions)
                .group_by(Offer.status, expired_flag)
            )
        ).all()
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
        # LEAST ignore les valeurs vides : une offre non notée reste hors des tranches.
        bucket = case((score.is_(None), None), else_=func.least(score / 5, 19))
        score_rows = (
            await session.execute(
                select(bucket, func.count()).where(*without_score).group_by(bucket)
            )
        ).all()
        canton_rows = (
            await session.execute(
                select(Offer.canton, func.count())
                .where(Offer.canton.is_not(None), *without_cantons)
                .group_by(Offer.canton)
            )
        ).all()
        basis_row = (
            await session.execute(
                select(
                    func.count().filter(sure),
                    func.count().filter(provisional),
                ).where(*without_basis)
            )
        ).one()

    live: dict[str, int] = {}
    for offer_status, expired, count in grouped:
        if not expired or offer_status in IN_PROGRESS:
            live[offer_status] = live.get(offer_status, 0) + count
    counts = OfferCounts(
        to_review=sum(live.get(s, 0) for s in TO_REVIEW),
        pending=pending,
        filtered_out=live.get(OfferStatus.FILTERED_OUT, 0),
        later=live.get(OfferStatus.LATER, 0),
        in_progress=sum(live.get(s, 0) for s in IN_PROGRESS),
        expired=sum(c for s, e, c in grouped if e and s not in IN_PROGRESS),
        all=sum(live.values()),
    )
    histogram = [0] * 20
    unscored = 0
    for index, count in score_rows:
        if index is None:
            unscored += count
        else:
            histogram[int(index)] += count
    facets = OfferFacets(
        scores=histogram,
        unscored=unscored,
        sure=int(basis_row[0]),
        provisional=int(basis_row[1]),
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
        criteria = await load_criteria(session)
    logos = await _logo_keys(runtime)
    return OfferPage(
        items=[
            _with_languages(
                _with_logo(_offer_out(o, links[o.id], evaluations.get(o.id), current_hash), logos),
                o,
                criteria,
            )
            for o in offers
        ],
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
        criteria = await load_criteria(session)
    links, evaluations = await _links(runtime, [offer_id]), await _evaluations(runtime, [offer_id])
    out = _offer_out(offer, links[offer_id], evaluations.get(offer_id), current_hash)
    return _with_languages(_with_logo(out, await _logo_keys(runtime)), offer, criteria)


def _with_languages(out: OfferOut, offer: Offer, criteria: Criteria) -> OfferOut:
    """« Langue à vérifier » (PR 17) : langues exigées par l'annonce, au niveau non renseigné."""
    text = f"{offer.title} {offer.description or offer.snippet or ''}"
    out.languages_to_check = languages_to_check(text, criteria)
    return out


async def _logo_keys(runtime: Runtime) -> set[str]:
    async with runtime.sessionmaker() as session:
        return set(
            await session.scalars(
                select(CompanyLogo.name_key).where(CompanyLogo.storage_key.is_not(None))
            )
        )


def _with_logo(out: OfferOut, logos: set[str]) -> OfferOut:
    if out.company and name_key(out.company) in logos:
        out.has_logo = True
    return out


@router.post(
    "/offers/{offer_id}/employer",
    operation_id="findEmployerOffer",
    responses={409: {"description": "IA indisponible ou plafond atteint"}},
)
async def find_employer_offer(request: Request, offer_id: int) -> OfferOut:
    """« Chercher l'offre chez l'employeur » (docs/20 §2) : site, outil de recrutement,
    puis Internet ; peut prendre une trentaine de secondes."""
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        if await session.get(Offer, offer_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
    try:
        await employer_service.find(runtime, offer_id)
    except employer_service.EmployerUnavailable as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    return await get_offer(request, offer_id)


@router.get(
    "/offers/{offer_id}/logo",
    operation_id="getOfferLogo",
    response_class=Response,
    responses={200: {"content": {"image/*": {}}}, 404: {"description": "Pas de logo"}},
)
async def get_offer_logo(request: Request, offer_id: int) -> Response:
    """Logo téléchargé par la plateforme ; le navigateur n'appelle aucun site tiers."""
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        company = await session.scalar(select(Offer.company).where(Offer.id == offer_id))
        logo = await session.get(CompanyLogo, name_key(company)) if company else None
    if logo is None or not logo.storage_key or not logo.media_type:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "pas de logo")
    try:
        data = runtime.storage.get(logo.storage_key)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "pas de logo") from None
    return Response(
        data,
        media_type=logo.media_type,
        headers={
            "Cache-Control": "private, max-age=86400",
            # Un SVG ne doit rien exécuter, même ouvert directement.
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
            "X-Content-Type-Options": "nosniff",
        },
    )


# « /collect » est bloqué par les bloqueurs de publicité (uBlock, EasyPrivacy), qui le
# prennent pour un traqueur d'audience : l'interface appelle « /alerts/refresh ».
@router.post("/collect", include_in_schema=False, status_code=status.HTTP_202_ACCEPTED)
@router.post(
    "/alerts/refresh",
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
