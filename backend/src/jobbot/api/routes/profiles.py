"""Profils d'essai (docs/17) : liste, création, duplication, renommage, suppression."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from jobbot.api.routes.news import Country, Language, NewsPreferences
from jobbot.db.models import Profile, ProfileSource
from jobbot.profiles import service
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

Name = Annotated[str, Field(min_length=1, max_length=60)]
Occupation = Annotated[str, Field(max_length=120)]


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class ProfileOut(BaseModel):
    id: int
    name: str
    occupation: str | None
    is_main: bool
    domain_keywords: list[str]
    sources: int


class ProfileList(BaseModel):
    # Profil choisi par le navigateur (en-tête X-Jobbot-Profile), sinon le principal.
    current_id: int
    items: list[ProfileOut]


class ProfileIn(BaseModel):
    name: Name
    occupation: Occupation | None = None
    domain_keywords: list[Annotated[str, Field(min_length=1, max_length=40)]] = Field(
        default_factory=list, max_length=30
    )
    countries: list[Country] = Field(default_factory=list, max_length=30)
    languages: list[Language] = Field(default_factory=list, max_length=5)


class ProfileUpdate(BaseModel):
    name: Name | None = None
    occupation: Occupation | None = None


async def _list(runtime: Runtime, header: str | None) -> ProfileList:
    async with runtime.sessionmaker.begin() as session:
        current = await service.resolve(session, header)
        counts = dict(
            (
                await session.execute(
                    select(ProfileSource.profile_id, func.count()).group_by(
                        ProfileSource.profile_id
                    )
                )
            ).all()
        )
        rows = list(
            await session.scalars(select(Profile).order_by(Profile.is_main.desc(), Profile.id))
        )
    return ProfileList(
        current_id=current.id,
        items=[
            ProfileOut(
                id=p.id,
                name=p.name,
                occupation=p.occupation,
                is_main=p.is_main,
                domain_keywords=list((p.preferences or {}).get("domain_keywords") or []),
                sources=counts.get(p.id, 0),
            )
            for p in rows
        ],
    )


@router.get("", operation_id="listProfiles")
async def list_profiles(request: Request) -> ProfileList:
    return await _list(_runtime(request), request.headers.get(service.HEADER))


@router.post("", operation_id="createProfile", status_code=status.HTTP_201_CREATED)
async def create_profile(request: Request, body: ProfileIn) -> ProfileList:
    """Profil fictif : nom, métier, « Mon domaine », pays et langues ; il suit au départ les
    articles « marché de l'emploi »."""
    preferences = NewsPreferences(
        domain_keywords=body.domain_keywords,
        domain_only=bool(body.domain_keywords),
        countries=body.countries,
        languages=body.languages,
    )
    async with _runtime(request).sessionmaker.begin() as session:
        await service.create(
            session,
            body.name.strip(),
            (body.occupation or "").strip() or None,
            preferences.model_dump(),
        )
    return await _list(_runtime(request), request.headers.get(service.HEADER))


@router.post(
    "/{profile_id}/duplicate", operation_id="duplicateProfile", status_code=status.HTTP_201_CREATED
)
async def duplicate_profile(request: Request, profile_id: int) -> ProfileList:
    """Copie d'un profil (préférences et sources), pour comparer deux variantes."""
    async with _runtime(request).sessionmaker.begin() as session:
        original = await session.get(Profile, profile_id)
        if original is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "profil introuvable")
        await service.create(
            session,
            f"{original.name} (copie)"[:60],
            original.occupation,
            dict(original.preferences or {}),
            copy_from=original,
        )
    return await _list(_runtime(request), request.headers.get(service.HEADER))


@router.patch("/{profile_id}", operation_id="updateProfile")
async def update_profile(request: Request, profile_id: int, body: ProfileUpdate) -> ProfileList:
    async with _runtime(request).sessionmaker.begin() as session:
        profile = await session.get(Profile, profile_id)
        if profile is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "profil introuvable")
        if body.name is not None:
            profile.name = body.name.strip() or profile.name
        if body.occupation is not None:
            profile.occupation = body.occupation.strip() or None
    return await _list(_runtime(request), request.headers.get(service.HEADER))


@router.delete(
    "/{profile_id}",
    operation_id="deleteProfile",
    responses={409: {"description": "Le profil principal ne se supprime pas"}},
)
async def delete_profile(request: Request, profile_id: int) -> ProfileList:
    async with _runtime(request).sessionmaker.begin() as session:
        profile = await session.get(Profile, profile_id)
        if profile is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "profil introuvable")
        if profile.is_main:
            raise HTTPException(status.HTTP_409_CONFLICT, "le profil principal ne se supprime pas")
        await session.delete(profile)
    return await _list(_runtime(request), request.headers.get(service.HEADER))
