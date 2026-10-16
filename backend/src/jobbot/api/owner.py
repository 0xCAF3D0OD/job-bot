"""Ce qui est commun à tous les comptes (sites d'emploi, catalogue des sources d'actualités)
ne se modifie que par l'exploitant, jusqu'aux réglages par compte (docs/65 §4)."""

from fastapi import HTTPException, status

from jobbot import accounts
from jobbot.runtime import Runtime

FORBIDDEN = "réservé à l'exploitant de la plateforme : ce réglage vaut pour tous les comptes"


async def require_owner(runtime: Runtime) -> None:
    async with runtime.sessionmaker() as session:
        if not await accounts.is_owner(session):
            raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN)
