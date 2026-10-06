"""Profils d'essai (docs/17) : profil choisi par le navigateur, création, sources de départ.

Le navigateur envoie le profil choisi dans l'en-tête `X-Jobbot-Profile` ; sans en-tête,
ou si le profil n'existe plus, c'est le profil principal. Pas de connexion : la plateforme
reste mono-utilisateur (docs/18 pour la connexion).
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import NewsSource, Profile, ProfileSource
from jobbot.news import catalog

HEADER = "X-Jobbot-Profile"
DEFAULT_PREFERENCES: dict[str, Any] = {
    "domain_keywords": [],
    "domain_only": False,
    "countries": [],
    "languages": [],
}


async def main_profile(session: AsyncSession) -> Profile:
    profile = await session.scalar(select(Profile).where(Profile.is_main.is_(True)))
    if profile is None:
        # Base sans profil (ne devrait pas arriver après la migration 0027) : on le recrée.
        profile = Profile(name="Profil principal", is_main=True, preferences={})
        session.add(profile)
        await session.flush()
    return profile


async def resolve(session: AsyncSession, header: str | None) -> Profile:
    """Profil choisi dans l'en-tête, sinon le principal."""
    if header and header.strip().isdigit():
        profile = await session.get(Profile, int(header.strip()))
        if profile is not None:
            return profile
    return await main_profile(session)


async def subscribe(session: AsyncSession, profile_id: int, source_id: int) -> None:
    if await session.get(ProfileSource, (profile_id, source_id)) is None:
        session.add(ProfileSource(profile_id=profile_id, source_id=source_id, active=True))


async def subscribe_starters(session: AsyncSession, profile_id: int) -> None:
    """Un nouveau profil suit les articles « marché de l'emploi » du catalogue (SECO, RTS…)."""
    for entry in catalog.load().sources:
        if entry.kind != "articles" or "emploi" not in entry.domains:
            continue
        source_id = await session.scalar(
            select(NewsSource.id).where(NewsSource.feed_url == entry.feed_url)
        )
        if source_id is None:
            source = NewsSource(
                kind=entry.kind,
                name=entry.name,
                url=entry.url,
                feed_url=entry.feed_url,
                match=entry.match,
                country=entry.country,
                language=entry.language,
                labour_market=entry.labour_market,
            )
            session.add(source)
            await session.flush()
            source_id = source.id
        await subscribe(session, profile_id, source_id)


async def create(
    session: AsyncSession,
    name: str,
    occupation: str | None,
    preferences: dict[str, Any],
    copy_from: Profile | None = None,
) -> Profile:
    """Nouveau profil d'essai ; copié d'un autre (préférences et sources), ou avec les sources
    de départ."""
    profile = Profile(
        name=name,
        occupation=occupation,
        is_main=False,
        preferences={**DEFAULT_PREFERENCES, **preferences},
    )
    session.add(profile)
    await session.flush()
    if copy_from is None:
        await subscribe_starters(session, profile.id)
    else:
        rows = await session.scalars(
            select(ProfileSource).where(ProfileSource.profile_id == copy_from.id)
        )
        for row in list(rows):
            session.add(
                ProfileSource(profile_id=profile.id, source_id=row.source_id, active=row.active)
            )
    return profile
