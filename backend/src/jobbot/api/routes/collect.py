"""Journal des recherches, offres collectées et lancement manuel de la collecte."""

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import ColumnElement, Time, and_, case, cast, func, not_, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.agency import (
    MARKED_AGENCIES,
    NO_CORRECTIONS,
    NOT_AGENCIES,
    AgencyKind,
    Corrections,
    Duplicate,
    agency_condition,
    agency_kind,
    company_key,
    duplicate,
    load_corrections,
    recent_applications,
)
from jobbot.core.contract import Contract
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
    Setting,
)
from jobbot.employer import service as employer_service
from jobbot.filtering.duplicates import applied_before, sent_on
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
    # « Écartée le 12 nov. » (§30 du 16.11) : vide hors d'un état écarté, et pour une offre écartée
    # avant la colonne.
    set_aside_at: datetime | None = None
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
    # Agence de placement (section 35 du 16.11, jobbot.agency) : agence connue, ou annonce « pour
    # notre client » ; vide si ce n'en est pas une, ou si tu l'as corrigé. Pour une agence, une
    # candidature envoyée ces 90 derniers jours à un poste proche.
    agency: Literal["known", "probable"] | None = None
    agency_duplicate: "AgencyDuplicateOut | None" = None
    # Doublon probable (décision de Kevin du 16.11) : une candidature au même titre chez la même
    # entreprise, envoyée depuis une autre fiche ou saisie dans Envoyées ; la plus récente. L'offre
    # reste visible avec la pastille « Déjà postulé le … ».
    applied_before: date | None = None
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
    # Passages de l'annonce qui correspondent au profil (score-v8) : retrouvés mot pour mot dans
    # l'annonce, surlignés dans le tri et dans le détail ; vide pour une note plus ancienne.
    passages: list[str] = []
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
    # Forme courte écrite sur les cartes de Trier (score-v9) : absente d'une note plus ancienne.
    short: str | None = None


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
    # « À traiter » avec les filtres de la liste, comme les autres compteurs (Kevin, 16.11) : la pastille du
    # panneau Filtres et le total de la liste disent le même nombre.
    pending: int
    # « À traiter » sans les filtres (count_pending) : « 12 sur 38 offres » au-dessus de la liste.
    pending_all: int
    filtered_out: int
    later: int
    # En préparation, candidature pas encore envoyée (expirées comprises : un bandeau le signale). Les envoyées
    # sont dans l'onglet Envoyées (section 38 du 16.11).
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


class AgencyDuplicateOut(BaseModel):
    title: str
    company: str
    sent_at: date


def _doubts(
    offer: Offer, evaluation: Evaluation | None, agency: AgencyKind | None = None
) -> list["DoubtOut"]:
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
    elif agency is not None:
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
            "passages": evaluation.passages or [],
            "scored_at": evaluation.scored_at,
            "score_stale": current_hash is not None and evaluation.profile_hash != current_hash,
        }
    return fields


def _offer_out(
    offer: Offer,
    links: list[OfferLinkOut],
    evaluation: Evaluation | None = None,
    current_hash: str | None = None,
    corrections: Corrections = NO_CORRECTIONS,
    sent: list[Duplicate] | None = None,
    posts: dict[tuple[str, str], list[tuple[date, int | None]]] | None = None,
) -> OfferOut:
    agency = agency_kind(offer, corrections)
    found = duplicate(offer, sent) if agency and sent else None
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
            "doubts": _doubts(offer, evaluation, agency),
            "agency": agency,
            "agency_duplicate": (
                {"title": found.title, "company": found.company, "sent_at": found.sent_at}
                if found
                else None
            ),
            "text_reading": text_reading(offer),
            "applied_before": sent_on(offer, posts or {}),
        }
    )


async def _sent_if_agency(
    session: AsyncSession, offers: Sequence[Offer], corrections: Corrections
) -> list[Duplicate]:
    """Les candidatures des 90 derniers jours, lues seulement si une offre est une agence."""
    if not any(agency_kind(o, corrections) for o in offers):
        return []
    return await recent_applications(session, datetime.now(LOCAL_TZ).date())


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
    # Filtre « Taux d'activité » (§65 du 17.11) : le nombre d'offres de chaque choix (« all »,
    # « 60 », « 80 », « 100 »), avec tous les autres filtres actifs mais sans celui du taux.
    rates: list[Facet] = []
    # Filtre « Contrat » (issue #468, Kevin, 18.11) : le nombre d'offres de chaque catégorie, « Non
    # précisé » compris et les catégories à 0 aussi, avec les autres filtres mais sans celui-ci.
    contracts: list[Facet] = []
    # Téléphone (Kevin, 18.11, choix a) : avec `hide_far`, les mêmes nombres sans les offres
    # « Loin » que la liste cache ; absent sinon.
    near: "NearFacets | None" = None


class NearFacets(BaseModel):
    """Les nombres des choix sans les offres « Loin » (note sous FAR_BELOW), que le téléphone
    cache tant qu'on ne les montre pas : Statut (« pending », « to_review », « later »,
    « in_progress »), Type de note, Taux et Contrat. Le choix actif égale alors « Afficher n
    offres »."""

    views: list[Facet]
    sure: int
    provisional: int
    rates: list[Facet]
    contracts: list[Facet] = []


# Les choix du filtre « Taux d'activité » (section 31 du 16.11) : dès 60, dès 80, 100 %.
RATE_CHOICES = (60, 80, 100)


def _rate_condition(min_rate: int) -> ColumnElement[bool]:
    """« Dès n % » : une offre sans taux connu reste visible."""
    return or_(Offer.rate_max.is_(None), Offer.rate_max >= min_rate)


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


def _doubtful(corrections: Corrections) -> ColumnElement[bool]:
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
        agency_condition(corrections),
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
    hide_agencies: bool = False,
    corrections: Corrections = NO_CORRECTIONS,
    contracts: Sequence[str] = (),
) -> list[ColumnElement[bool]]:
    """Filtres d'affichage : ils changent ce que l'on voit, n'écartent rien (docs/06 §7).
    Un doublon n'apparaît jamais : son offre gardée porte tous ses liens (docs/30 §3)."""
    conditions: list[ColumnElement[bool]] = [Offer.duplicate_of.is_(None)]
    if hide_doubtful:
        conditions.append(_doubtful(corrections).is_(False))
    if hide_agencies:
        # « Masquer les agences de placement » (section 35 du 16.11) : les mêmes que la pastille.
        conditions.append(not_(agency_condition(corrections)))
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
        conditions.append(_rate_condition(min_rate))
    if contracts:
        # Plusieurs choix : l'une des catégories. « Non précisé » est un choix comme les autres,
        # jamais une offre écartée en silence.
        conditions.append(Offer.contract.in_(contracts))
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
        # En préparation seulement : les candidatures envoyées sont dans Envoyées (section 38 du 16.11).
        return Offer.status == OfferStatus.PREPARING
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
    hide_agencies: bool = False,
    with_filtered_out: bool = False,
    with_expired: bool = False,
    basis: Literal["sure", "provisional"] | None = None,
    contracts: Annotated[list[Contract], Query(max_length=5)] = [],  # noqa: B006
    hide_far: bool = False,
) -> OfferPage:
    """`recent` : dernières offres apparues ; `popular` : offres vues dans le plus d'alertes ;
    `score` : meilleure note de l'IA d'abord (offres non notées à la fin).
    `view` : à examiner, écartées par le filtre, ou toutes. Les autres paramètres sont des
    filtres d'affichage ; les compteurs par statut et les facettes en tiennent compte."""
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        corrections = await load_corrections(session)
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
    conditions = _filters(
        q,
        sources,
        cantons,
        min_rate,
        external_only,
        remote,
        hide_doubtful,
        hide_agencies,
        corrections,
        contracts,
    )
    filtered = len(conditions)
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
    # Téléphone (Kevin, 18.11, choix a) : sans filtre de note, la liste cache les offres « Loin »
    # (note sous FAR_BELOW) et « Afficher n offres » ne les compte pas. Les nombres sous les choix
    # (Statut, Type de note, Taux) les retirent aussi : le choix actif égale toujours le bouton.
    # Une offre pas encore notée reste visible. La liste et son total ne changent pas.
    near: list[ColumnElement[bool]] = (
        [or_(score.is_(None), score >= FAR_BELOW)]
        if hide_far and min_score is None and max_score is None
        else []
    )
    without_basis = [*conditions, *([view_condition] if view_condition is not None else [])]
    if basis is not None:
        conditions.append(provisional if basis == "provisional" else sure)
    listed = [*conditions, *([view_condition] if view_condition is not None else [])]
    # Facettes : calculées sans le filtre qu'elles décrivent, pour pouvoir élargir le choix.
    without_sources = _filters(
        q,
        [],
        cantons,
        min_rate,
        external_only,
        remote,
        hide_doubtful,
        hide_agencies,
        corrections,
        contracts,
    )
    without_cantons = _filters(
        q,
        sources,
        [],
        min_rate,
        external_only,
        remote,
        hide_doubtful,
        hide_agencies,
        corrections,
        contracts,
    )
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
    # Sans le filtre du taux : les nombres sous chaque choix (§65), le choix actif donnant le
    # même nombre que « Afficher n offres ». Les filtres de note et de type de note restent.
    without_rate = [
        *_filters(
            q,
            sources,
            cantons,
            None,
            external_only,
            remote,
            hide_doubtful,
            hide_agencies,
            corrections,
            contracts,
        ),
        *conditions[filtered:],
        *([view_condition] if view_condition is not None else []),
    ]
    # Sans le filtre du contrat, de la même façon : « CDI · 120 », le total des choix cochés
    # donnant « Afficher n offres ».
    without_contract = [
        *_filters(
            q,
            sources,
            cantons,
            min_rate,
            external_only,
            remote,
            hide_doubtful,
            hide_agencies,
            corrections,
        ),
        *conditions[filtered:],
        *([view_condition] if view_condition is not None else []),
    ]

    async with runtime.sessionmaker() as session:
        # « À traiter » sans les filtres : « 12 sur 38 offres », une seule source (docs/139).
        pending_all = await count_pending(session)
        # « À traiter » avec les filtres : la pastille du panneau, le même nombre que la liste.
        pending_condition = _view_condition("pending", with_filtered_out, with_expired)
        pending = int(
            await session.scalar(
                select(func.count()).select_from(Offer).where(*conditions, pending_condition)
            )
            or 0
        )
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
        rate_row = (
            await session.execute(
                select(
                    func.count(),
                    *(func.count().filter(_rate_condition(rate)) for rate in RATE_CHOICES),
                ).where(*without_rate)
            )
        ).one()
        contract_rows = dict(
            (
                await session.execute(
                    select(Offer.contract, func.count())
                    .where(*without_contract)
                    .group_by(Offer.contract)
                )
            ).all()
        )
        near_facets: NearFacets | None = None
        if near:
            near_rows = (
                await session.execute(
                    select(Offer.status, expired_flag, func.count())
                    .where(*conditions, *near)
                    .group_by(Offer.status, expired_flag)
                )
            ).all()
            near_pending = int(
                await session.scalar(
                    select(func.count())
                    .select_from(Offer)
                    .where(*conditions, *near, pending_condition)
                )
                or 0
            )
            near_basis = (
                await session.execute(
                    select(func.count().filter(sure), func.count().filter(provisional)).where(
                        *without_basis, *near
                    )
                )
            ).one()
            near_rate = (
                await session.execute(
                    select(
                        func.count(),
                        *(func.count().filter(_rate_condition(rate)) for rate in RATE_CHOICES),
                    ).where(*without_rate, *near)
                )
            ).one()
            near_contracts = dict(
                (
                    await session.execute(
                        select(Offer.contract, func.count())
                        .where(*without_contract, *near)
                        .group_by(Offer.contract)
                    )
                ).all()
            )
            near_live: dict[str, int] = {}
            for offer_status, expired, count in near_rows:
                if not expired or offer_status in IN_PROGRESS:
                    near_live[offer_status] = near_live.get(offer_status, 0) + count
            near_facets = NearFacets(
                views=[
                    Facet(value="pending", count=near_pending),
                    Facet(value="to_review", count=sum(near_live.get(s, 0) for s in TO_REVIEW)),
                    Facet(value="later", count=near_live.get(OfferStatus.LATER, 0)),
                    Facet(value="in_progress", count=near_live.get(OfferStatus.PREPARING, 0)),
                ],
                sure=int(near_basis[0]),
                provisional=int(near_basis[1]),
                rates=[
                    Facet(value=str(value), count=int(count))
                    for value, count in zip(
                        ("all", *map(str, RATE_CHOICES)), near_rate, strict=True
                    )
                ],
                contracts=[
                    Facet(value=contract.value, count=int(near_contracts.get(contract.value, 0)))
                    for contract in Contract
                ],
            )

    live: dict[str, int] = {}
    for offer_status, expired, count in grouped:
        if not expired or offer_status in IN_PROGRESS:
            live[offer_status] = live.get(offer_status, 0) + count
    counts = OfferCounts(
        to_review=sum(live.get(s, 0) for s in TO_REVIEW),
        pending=pending,
        pending_all=pending_all,
        filtered_out=live.get(OfferStatus.FILTERED_OUT, 0),
        later=live.get(OfferStatus.LATER, 0),
        in_progress=live.get(OfferStatus.PREPARING, 0),
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
        rates=[
            Facet(value=str(value), count=int(count))
            for value, count in zip(("all", *map(str, RATE_CHOICES)), rate_row, strict=True)
        ],
        contracts=[
            Facet(value=contract.value, count=int(contract_rows.get(contract.value, 0)))
            for contract in Contract
        ],
        near=near_facets,
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
        recent = await _sent_if_agency(session, offers, corrections)
        posts = await applied_before(session)
    logos = await _logo_keys(runtime)
    return OfferPage(
        items=[
            _with_languages(
                _with_logo(
                    _offer_out(
                        o,
                        links[o.id],
                        evaluations.get(o.id),
                        current_hash,
                        corrections,
                        recent,
                        posts,
                    ),
                    logos,
                ),
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
        corrections = await load_corrections(session)
        sent = await _sent_if_agency(session, [offer], corrections)
        posts = await applied_before(session)
    links, evaluations = await _links(runtime, [offer_id]), await _evaluations(runtime, [offer_id])
    out = _offer_out(
        offer, links[offer_id], evaluations.get(offer_id), current_hash, corrections, sent, posts
    )
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


async def _correct_agency(request: Request, offer_id: int, *, agency: bool, keep: bool) -> OfferOut:
    """« Ce n'est pas une agence » (section 35 du 16.11) et « C'est une agence de placement »
    (Kevin, 16.11 23 h 33) : gardés pour l'entreprise de l'offre, dans ce compte seulement
    (réglages `not_agencies` et `agencies`). La dernière correction l'emporte : elle retire
    l'entreprise de l'autre liste. `keep=False` revient sur la correction. L'offre est relue sous
    la RLS du compte (C-5) : celle d'un autre compte donne 404."""
    async with _runtime(request).sessionmaker.begin() as session:
        offer = await session.get(Offer, offer_id)
        key = company_key(offer.company) if offer is not None else ""
        if offer is None or not key:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "offre introuvable")
        current = await load_corrections(session)
        mine, other = (current.yes, current.no) if agency else (current.no, current.yes)
        lists = {
            MARKED_AGENCIES if agency else NOT_AGENCIES: mine | {key} if keep else mine - {key},
            NOT_AGENCIES if agency else MARKED_AGENCIES: other - {key} if keep else other,
        }
        for name, names in lists.items():
            value = sorted(names)
            await session.execute(
                pg_insert(Setting)
                .values(key=name, value=value)
                .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": value})
            )
    return await get_offer(request, offer_id)


@router.post("/offers/{offer_id}/not-agency", operation_id="markNotAgency")
async def mark_not_agency(request: Request, offer_id: int) -> OfferOut:
    return await _correct_agency(request, offer_id, agency=False, keep=True)


@router.delete("/offers/{offer_id}/not-agency", operation_id="unmarkNotAgency")
async def unmark_not_agency(request: Request, offer_id: int) -> OfferOut:
    return await _correct_agency(request, offer_id, agency=False, keep=False)


@router.post("/offers/{offer_id}/agency", operation_id="markAgency")
async def mark_agency(request: Request, offer_id: int) -> OfferOut:
    return await _correct_agency(request, offer_id, agency=True, keep=True)


@router.delete("/offers/{offer_id}/agency", operation_id="unmarkAgency")
async def unmark_agency(request: Request, offer_id: int) -> OfferOut:
    return await _correct_agency(request, offer_id, agency=True, keep=False)


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
