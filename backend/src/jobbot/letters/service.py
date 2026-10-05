"""Accès aux brouillons de lettre et aux coordonnées, partagé par les routes."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import Draft, DraftKind, Setting
from jobbot.letters.document import Identity

IDENTITY_KEYS = {
    "name": "identity_name",
    "street": "identity_street",
    "postcode": "identity_postcode",
    "city": "identity_city",
    "phone": "identity_phone",
    "email": "identity_email",
}


async def load_identity(session: AsyncSession) -> Identity:
    rows = {
        s.key: s.value
        for s in await session.scalars(
            select(Setting).where(Setting.key.in_(IDENTITY_KEYS.values()))
        )
    }
    return Identity(**{field: rows.get(key) for field, key in IDENTITY_KEYS.items()})


async def current_draft(
    session: AsyncSession, offer_id: int, kind: str = DraftKind.LETTER
) -> Draft | None:
    """La version qui compte : la dernière modifiée ou, à défaut, la dernière rédigée."""
    return await session.scalar(
        select(Draft)
        .where(Draft.offer_id == offer_id, Draft.kind == kind)
        .order_by(func.coalesce(Draft.edited_at, Draft.created_at).desc(), Draft.version.desc())
        .limit(1)
    )
