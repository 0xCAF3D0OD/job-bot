"""Profils d'essai (docs/17) : profil choisi par le navigateur, création.

Le navigateur envoie le profil choisi dans l'en-tête `X-Jobbot-Profile` ; sans en-tête,
ou si le profil n'existe plus, c'est le profil principal. Pas de connexion : la plateforme
reste mono-utilisateur (docs/18 pour la connexion).
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import Profile

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
        # Compte invité, à sa première visite (docs/65) : son profil.
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


async def create(
    session: AsyncSession,
    name: str,
    occupation: str | None,
    preferences: dict[str, Any],
) -> Profile:
    """Nouveau profil d'essai, avec ses préférences (celles d'un autre pour une copie)."""
    profile = Profile(
        name=name,
        occupation=occupation,
        is_main=False,
        preferences={**DEFAULT_PREFERENCES, **preferences},
    )
    session.add(profile)
    await session.flush()
    return profile
