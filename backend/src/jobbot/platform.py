"""Réglages de l'installation, communs à tous les comptes (docs/65 §4)."""

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import PlatformSetting

# Plafond de l'IA d'un compte invité, tant que l'exploitant n'en fixe pas un autre ; et plafond
# total de la plateforme, tous comptes confondus.
ACCOUNT_AI_BUDGET_CHF = Decimal("5")
TOTAL_AI_BUDGET_CHF = Decimal("50")


async def get(session: AsyncSession, key: str, default: Any = None) -> Any:
    value = await session.scalar(select(PlatformSetting.value).where(PlatformSetting.key == key))
    return default if value is None else value


async def put(session: AsyncSession, key: str, value: Any) -> None:
    await session.execute(
        insert(PlatformSetting)
        .values(key=key, value=value)
        .on_conflict_do_update(index_elements=["key"], set_={"value": value})
    )


async def total_ai_budget(session: AsyncSession) -> Decimal:
    return Decimal(str(await get(session, "ai_total_budget_chf", str(TOTAL_AI_BUDGET_CHF))))
