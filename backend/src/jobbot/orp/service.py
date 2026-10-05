"""Données ORP partagées par la page ORP, la page Aujourd'hui et les rappels (docs/09)."""

from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.core.orp import DEFAULT_DUE_DAY
from jobbot.db.models import Application, Setting


async def load_due_day(session: AsyncSession) -> int:
    """Jour de remise du mois suivant (Réglages, 5 par défaut)."""
    value = await session.scalar(select(Setting.value).where(Setting.key == "orp_due_day"))
    return int(value) if value else DEFAULT_DUE_DAY


async def load_target(session: AsyncSession) -> int | None:
    value = await session.scalar(select(Setting.value).where(Setting.key == "orp_monthly_target"))
    return int(value) if value else None


@dataclass(frozen=True)
class MonthCounts:
    count: int
    # Lignes sans adresse d'entreprise : « à compléter » avant la remise.
    incomplete: int


async def month_counts(session: AsyncSession, month: str) -> MonthCounts:
    in_month = Application.orp_month == month
    count = await session.scalar(select(func.count()).select_from(Application).where(in_month))
    incomplete = await session.scalar(
        select(func.count())
        .select_from(Application)
        .where(
            in_month,
            or_(
                Application.company_address.is_(None),
                func.btrim(Application.company_address) == "",
            ),
        )
    )
    return MonthCounts(count or 0, incomplete or 0)
