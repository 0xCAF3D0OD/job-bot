"""Prérequis (filtre) et réglages, saisis dans l'interface (docs/04 §3 et §6)."""

from datetime import UTC, datetime
from typing import Annotated, Literal

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from jobbot import accounts
from jobbot.core.filter import (
    CONTRACT_KEYWORDS,
    LANGUAGE_NAMES,
    REQUIREMENT_WORDS,
    ContractType,
    Criteria,
    Language,
    RemotePolicy,
)
from jobbot.db.models import Criterion, Setting
from jobbot.filtering.service import load_criteria, save_criteria
from jobbot.notify import service as notify_service
from jobbot.runtime import Runtime
from jobbot.scoring.service import budget_details
from jobbot.worker.queue import enqueue
from jobbot.worker.tasks.filter import FILTER_JOB

router = APIRouter(prefix="/api", tags=["preferences"])

ShortText = Annotated[str, Field(min_length=1, max_length=80)]


def _clean(values: list[str]) -> list[str]:
    seen: dict[str, str] = {}
    for value in values:
        stripped = value.strip()
        if stripped and stripped.casefold() not in seen:
            seen[stripped.casefold()] = stripped
    return list(seen.values())


class CriteriaIn(BaseModel):
    locations: list[ShortText] = Field(default_factory=list, max_length=100)
    # Télétravail complet (docs/26 §3) : refusé, ouvert depuis la Suisse, ou partout.
    remote_policy: RemotePolicy = RemotePolicy.REFUSE
    min_rate: int | None = Field(default=None, ge=1, le=100)
    excluded_types: list[ContractType] = Field(default_factory=list)
    banned_words: list[ShortText] = Field(default_factory=list, max_length=100)
    unspoken_languages: list[Language] = Field(default_factory=list)

    @field_validator("locations", "banned_words")
    @classmethod
    def _dedupe(cls, values: list[str]) -> list[str]:
        return _clean(values)


class KeywordsOut(BaseModel):
    """Mots-clés cherchés par le filtre, affichés sous chaque case du formulaire."""

    contract_types: dict[ContractType, list[str]]
    language_names: dict[Language, list[str]]
    requirement_words: list[str]


class CriteriaOut(BaseModel):
    criteria: CriteriaIn
    keywords: KeywordsOut
    # Date du premier enregistrement ; None tant que Kevin ne les a jamais saisis : la page
    # montre alors le formulaire, ensuite un résumé et un bouton « Modifier » (docs/10 §2).
    saved_at: datetime | None = None


class FilterResponse(BaseModel):
    result: Literal["queued", "already_queued"]


class SettingsModel(BaseModel):
    orp_monthly_target: int | None = Field(default=None, ge=1, le=100)
    notify_score_threshold: int = Field(default=70, ge=0, le=100)
    llm_monthly_budget_chf: float = Field(default=10, ge=0, le=1000)
    # Jour de remise des preuves ORP du mois précédent (docs/09 §5).
    orp_due_day: int = Field(default=5, ge=2, le=28)
    # Recherche automatique de l'annonce chez l'employeur dès cette note (docs/20 §2.1).
    employer_search_threshold: int = Field(default=70, ge=0, le=100)


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


def _keywords() -> KeywordsOut:
    return KeywordsOut(
        contract_types={k: list(v) for k, v in CONTRACT_KEYWORDS.items()},
        language_names={k: list(v) for k, v in LANGUAGE_NAMES.items()},
        requirement_words=list(REQUIREMENT_WORDS),
    )


def _criteria_in(criteria: Criteria) -> CriteriaIn:
    return CriteriaIn(
        locations=list(criteria.locations),
        remote_policy=criteria.remote_policy,
        min_rate=criteria.min_rate,
        excluded_types=list(criteria.excluded_types),
        banned_words=list(criteria.banned_words),
        unspoken_languages=list(criteria.unspoken_languages),
    )


@router.get("/criteria", operation_id="getCriteria")
async def get_criteria(request: Request) -> CriteriaOut:
    async with _runtime(request).sessionmaker() as session:
        criteria = await load_criteria(session)
        saved_at = await session.scalar(select(func.min(Criterion.updated_at)))
    return CriteriaOut(criteria=_criteria_in(criteria), keywords=_keywords(), saved_at=saved_at)


@router.put("/criteria", operation_id="saveCriteria")
async def put_criteria(request: Request, body: CriteriaIn) -> CriteriaOut:
    """Enregistre les prérequis et relance le filtre sur les offres non triées à la main."""
    runtime = _runtime(request)
    criteria = Criteria(
        locations=tuple(body.locations),
        remote_policy=body.remote_policy,
        min_rate=body.min_rate,
        excluded_types=tuple(body.excluded_types),
        banned_words=tuple(body.banned_words),
        unspoken_languages=tuple(body.unspoken_languages),
    )
    async with runtime.sessionmaker.begin() as session:
        await save_criteria(session, criteria)
        saved_at = await session.scalar(select(func.min(Criterion.updated_at)))
    await enqueue(runtime.settings, FILTER_JOB)
    return CriteriaOut(criteria=_criteria_in(criteria), keywords=_keywords(), saved_at=saved_at)


@router.post("/filter", operation_id="startFilter", status_code=status.HTTP_202_ACCEPTED)
async def start_filter(request: Request) -> FilterResponse:
    queued = await enqueue(_runtime(request).settings, FILTER_JOB)
    return FilterResponse(result="queued" if queued else "already_queued")


@router.get("/settings", operation_id="getSettings")
async def get_settings(request: Request) -> SettingsModel:
    async with _runtime(request).sessionmaker() as session:
        rows = {s.key: s.value for s in await session.scalars(select(Setting))}
        if not await accounts.is_owner(session):
            # Compte invité : le plafond de l'IA est celui que l'exploitant a fixé (docs/65 §4).
            rows["llm_monthly_budget_chf"] = float(
                (await budget_details(session, datetime.now(UTC))).cap
            )
    return SettingsModel.model_validate(
        {k: v for k, v in rows.items() if k in SettingsModel.model_fields}
    )


@router.put("/settings", operation_id="saveSettings")
async def put_settings(request: Request, body: SettingsModel) -> SettingsModel:
    async with _runtime(request).sessionmaker.begin() as session:
        values = body.model_dump()
        if not await accounts.is_owner(session):
            # Fixé par l'exploitant : un compte invité ne le change pas.
            values.pop("llm_monthly_budget_chf")
        for key, value in values.items():
            await session.execute(
                insert(Setting)
                .values(key=key, value=value)
                .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": value})
            )
    return await get_settings(request)


# --- Filtres affichés sur la page Offres (docs/10 §3) -----------------------------------

FilterKey = Literal["score", "remote", "sources", "cantons", "rate", "external", "doubtful"]
ALL_FILTERS: list[FilterKey] = [
    "score",
    "remote",
    "sources",
    "cantons",
    "rate",
    "external",
    "doubtful",
]
# Filtres ajoutés après la personnalisation (docs/10 §3) : visibles chez qui l'avait faite.
ADDED_LATER: list[FilterKey] = ["remote", "doubtful"]


class OfferFiltersVisible(BaseModel):
    """Filtres affichés dans le panneau ; statut, recherche et tri le sont toujours."""

    visible: list[FilterKey]

    @field_validator("visible")
    @classmethod
    def _ordered(cls, values: list[FilterKey]) -> list[FilterKey]:
        return [key for key in ALL_FILTERS if key in values]


@router.get("/offer-filters", operation_id="getOfferFilters")
async def get_offer_filters(request: Request) -> OfferFiltersVisible:
    async with _runtime(request).sessionmaker() as session:
        value = await session.scalar(
            select(Setting.value).where(Setting.key == "offer_filters_visible")
        )
        known = await session.scalar(
            select(Setting.value).where(Setting.key == "offer_filters_known")
        )
    # Par défaut, tous les filtres, comme avant.
    if not isinstance(value, list):
        return OfferFiltersVisible(visible=ALL_FILTERS)
    # Un filtre ajouté depuis ton choix (« Télétravail », docs/26 §4) apparaît : tu ne l'avais
    # pas masqué. Les listes enregistrées avant cette règle connaissaient les filtres d'avant.
    seen = known if isinstance(known, list) else [f for f in ALL_FILTERS if f not in ADDED_LATER]
    added = [f for f in ALL_FILTERS if f not in seen]
    return OfferFiltersVisible(visible=[*value, *added])


@router.put("/offer-filters", operation_id="saveOfferFilters")
async def put_offer_filters(request: Request, body: OfferFiltersVisible) -> OfferFiltersVisible:
    async with _runtime(request).sessionmaker.begin() as session:
        await session.execute(
            insert(Setting)
            .values(key="offer_filters_visible", value=body.visible)
            .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": body.visible})
        )
        await session.execute(
            insert(Setting)
            .values(key="offer_filters_known", value=ALL_FILTERS)
            .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": ALL_FILTERS})
        )
    return body


# --- Notifications (0.4.0-c) -----------------------------------------------------------


class NotificationsStatus(BaseModel):
    configured: bool
    # Serveur ntfy (sans le sujet de l'installation, qui est secret).
    server: str
    # Compte invité (docs/65 §4) : son propre sujet, qu'il active lui-même et qu'il suit dans
    # l'application ntfy ; vide pour l'exploitant, dont le sujet est celui de l'installation.
    personal: bool = False
    topic: str | None = None


class PhoneIn(BaseModel):
    enabled: bool


@router.get("/notifications", operation_id="getNotifications")
async def get_notifications(request: Request) -> NotificationsStatus:
    runtime = _runtime(request)
    settings = runtime.settings
    async with runtime.sessionmaker() as session:
        if await accounts.is_owner(session):
            return NotificationsStatus(
                configured=settings.ntfy_configured, server=settings.ntfy_url
            )
        topic = await session.scalar(
            select(Setting.value).where(Setting.key == notify_service.PHONE_TOPIC)
        )
    return NotificationsStatus(
        configured=bool(topic), server=settings.ntfy_url, personal=True, topic=topic or None
    )


@router.put(
    "/notifications/phone",
    operation_id="setPhoneNotifications",
    responses={409: {"description": "Réglage d'installation pour l'exploitant"}},
)
async def set_phone(request: Request, body: PhoneIn) -> NotificationsStatus:
    """Compte invité : recevoir ses alertes sur son téléphone, avec un sujet ntfy à lui."""
    runtime = _runtime(request)
    async with runtime.sessionmaker.begin() as session:
        if await accounts.is_owner(session):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "ton sujet ntfy est un réglage d'installation (README)"
            )
        if body.enabled:
            topic = notify_service.new_topic()
            await session.execute(
                insert(Setting)
                .values(key=notify_service.PHONE_TOPIC, value=topic)
                .on_conflict_do_nothing(index_elements=["user_id", "key"])
            )
        else:
            await session.execute(delete(Setting).where(Setting.key == notify_service.PHONE_TOPIC))
    return await get_notifications(request)


@router.post(
    "/notifications/test",
    operation_id="testNotification",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={409: {"description": "Non configuré"}, 502: {"description": "Envoi refusé"}},
)
async def test_notification(request: Request) -> None:
    runtime = _runtime(request)
    async with runtime.sessionmaker() as session:
        target = await notify_service.phone_settings(session, runtime.settings)
    if target is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "notifications non configurées")
    try:
        await notify_service.send_test(target)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"envoi refusé par le serveur ntfy ({type(exc).__name__})"
        ) from None
