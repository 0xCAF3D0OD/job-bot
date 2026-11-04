"""« Mon domaine » (docs/16 §2-3) : les mots du domaine, lus par Formations et l'accueil.

Les Actualités ont quitté la plateforme (docs/135, 1.6.25) ; seuls ces réglages restent. Les tables
news_sources, news_items et profile_sources sont gardées, sans lecteur ni rédacteur.
"""

from typing import Annotated

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from jobbot.db.models import Profile
from jobbot.news import domain
from jobbot.news.language import LANGUAGES
from jobbot.profiles import service as profiles
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/news", tags=["news"])
# Pays : code ISO à deux lettres, ou INT pour international.
Country = Annotated[str, Field(pattern=r"^([A-Z]{2}|INT)$")]
Language = Annotated[str, Field(pattern=r"^[a-z]{2}$")]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class NewsPreferences(BaseModel):
    """« Mon domaine » et filtres, retenus d'une visite à l'autre (docs/16 §2-3)."""

    domain_keywords: list[Annotated[str, Field(min_length=1, max_length=40)]] = Field(
        max_length=domain.MAX_KEYWORDS
    )
    domain_only: bool
    countries: list[Country] = Field(max_length=30)
    languages: list[Language] = Field(max_length=len(LANGUAGES))

    @field_validator("domain_keywords")
    @classmethod
    def _dedupe(cls, values: list[str]) -> list[str]:
        seen: dict[str, str] = {}
        for value in values:
            stripped = value.strip()
            if stripped and stripped.casefold() not in seen:
                seen[stripped.casefold()] = stripped
        return list(seen.values())


async def _profile(request: Request) -> Profile:
    """Profil choisi par le navigateur (docs/17), sinon le principal."""
    async with _runtime(request).sessionmaker.begin() as session:
        return await profiles.resolve(session, request.headers.get(profiles.HEADER))


async def _preferences(runtime: Runtime, profile: Profile) -> NewsPreferences:
    """Réglages du profil ; à la première lecture du profil principal, « Mon domaine » est
    pré-rempli depuis les offres postulées ou bien notées, une seule fois."""
    saved = profile.preferences if isinstance(profile.preferences, dict) else {}
    if "domain_keywords" in saved or not profile.is_main:
        return NewsPreferences.model_validate({**profiles.DEFAULT_PREFERENCES, **saved})
    async with runtime.sessionmaker.begin() as session:
        preferences = NewsPreferences.model_validate(
            {**profiles.DEFAULT_PREFERENCES, "domain_keywords": await domain.suggest(session)}
        )
        stored = await session.get(Profile, profile.id)
        if stored is not None:
            stored.preferences = preferences.model_dump()
    return preferences


@router.get("/preferences", operation_id="getNewsPreferences")
async def get_preferences(request: Request) -> NewsPreferences:
    return await _preferences(_runtime(request), await _profile(request))


@router.put("/preferences", operation_id="saveNewsPreferences")
async def save_preferences(request: Request, body: NewsPreferences) -> NewsPreferences:
    profile = await _profile(request)
    async with _runtime(request).sessionmaker.begin() as session:
        stored = await session.get(Profile, profile.id)
        if stored is not None:
            stored.preferences = body.model_dump()
    return body
