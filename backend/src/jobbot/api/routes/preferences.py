"""Prérequis (filtre) et réglages, saisis dans l'interface (docs/04 §3 et §6)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from jobbot.core.filter import (
    CONTRACT_KEYWORDS,
    LANGUAGE_NAMES,
    REQUIREMENT_WORDS,
    ContractType,
    Criteria,
    Language,
)
from jobbot.db.models import Setting
from jobbot.filtering.service import load_criteria, save_criteria
from jobbot.runtime import Runtime
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
    remote_ok: bool = False
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


class FilterResponse(BaseModel):
    result: Literal["queued", "already_queued"]


class SettingsModel(BaseModel):
    orp_monthly_target: int | None = Field(default=None, ge=1, le=100)
    notify_score_threshold: int = Field(default=70, ge=0, le=100)
    llm_monthly_budget_chf: float = Field(default=10, ge=0, le=1000)


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
        remote_ok=criteria.remote_ok,
        min_rate=criteria.min_rate,
        excluded_types=list(criteria.excluded_types),
        banned_words=list(criteria.banned_words),
        unspoken_languages=list(criteria.unspoken_languages),
    )


@router.get("/criteria", operation_id="getCriteria")
async def get_criteria(request: Request) -> CriteriaOut:
    async with _runtime(request).sessionmaker() as session:
        criteria = await load_criteria(session)
    return CriteriaOut(criteria=_criteria_in(criteria), keywords=_keywords())


@router.put("/criteria", operation_id="saveCriteria")
async def put_criteria(request: Request, body: CriteriaIn) -> CriteriaOut:
    """Enregistre les prérequis et relance le filtre sur les offres non triées à la main."""
    runtime = _runtime(request)
    criteria = Criteria(
        locations=tuple(body.locations),
        remote_ok=body.remote_ok,
        min_rate=body.min_rate,
        excluded_types=tuple(body.excluded_types),
        banned_words=tuple(body.banned_words),
        unspoken_languages=tuple(body.unspoken_languages),
    )
    async with runtime.sessionmaker.begin() as session:
        await save_criteria(session, criteria)
    await enqueue(runtime.settings, FILTER_JOB)
    return CriteriaOut(criteria=_criteria_in(criteria), keywords=_keywords())


@router.post("/filter", operation_id="startFilter", status_code=status.HTTP_202_ACCEPTED)
async def start_filter(request: Request) -> FilterResponse:
    queued = await enqueue(_runtime(request).settings, FILTER_JOB)
    return FilterResponse(result="queued" if queued else "already_queued")


@router.get("/settings", operation_id="getSettings")
async def get_settings(request: Request) -> SettingsModel:
    async with _runtime(request).sessionmaker() as session:
        rows = {s.key: s.value for s in await session.scalars(select(Setting))}
    return SettingsModel.model_validate(
        {k: v for k, v in rows.items() if k in SettingsModel.model_fields}
    )


@router.put("/settings", operation_id="saveSettings")
async def put_settings(request: Request, body: SettingsModel) -> SettingsModel:
    async with _runtime(request).sessionmaker.begin() as session:
        for key, value in body.model_dump().items():
            await session.execute(
                insert(Setting)
                .values(key=key, value=value)
                .on_conflict_do_update(index_elements=["key"], set_={"value": value})
            )
    return body
