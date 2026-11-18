"""« Ton nom sur la feuille » (LISEZMOI §70, planche FeuilleNom ; Kevin, 18.11.2026) : ton nom, ton
conseiller ORP et ton office régional, gardés dans ton compte pour la feuille du rendez-vous.

Niveau (docs/regles-securite-donnees.md, D-1) : le nom est une donnée **personnelle** ; le
conseiller et l'office régional disent que tu es suivi par l'ORP, donc **sensibles** (données
ORP). Rangés dans la table `settings` du compte : cloisonnés par la RLS (C-1), dans l'export
(V-2), effacés avec le compte (V-3). Jamais journalisés (J-1), jamais envoyés à l'IA (I-1). Un
champ vidé est retiré, pas gardé vide.

Le conseiller est pré-rempli par celui du rendez-vous s'il est connu, tant que tu n'en as pas
écrit ou vidé un.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot.db.models import OrpMeeting, Setting
from jobbot.orp.meeting import next_meeting

# Les trois champs de la page et leur clé dans `settings`.
KEYS = {"name": "orp_sheet_name", "advisor": "orp_sheet_advisor", "office": "orp_sheet_office"}


@dataclass
class SheetIdentity:
    name: str | None
    advisor: str | None
    office: str | None


async def _meeting_advisor(session: AsyncSession) -> str | None:
    """Le conseiller du prochain rendez-vous, sinon du dernier qui en nomme un."""
    upcoming = await next_meeting(session, datetime.now(UTC))
    if upcoming is not None and upcoming.advisor:
        return upcoming.advisor
    advisor: str | None = await session.scalar(
        select(OrpMeeting.advisor)
        .where(OrpMeeting.advisor.is_not(None))
        .order_by(OrpMeeting.starts_at.desc())
        .limit(1)
    )
    return advisor


async def load(session: AsyncSession) -> SheetIdentity:
    rows = (
        await session.execute(
            select(Setting.key, Setting.value).where(Setting.key.in_(KEYS.values()))
        )
    ).all()
    saved = {key: value for key, value in rows if isinstance(value, str)}
    # Un conseiller vidé à la main reste vide (« "" ») : le rendez-vous ne le remplit plus.
    advisor = saved.get(KEYS["advisor"])
    if advisor is None:
        advisor = await _meeting_advisor(session)
    return SheetIdentity(
        name=saved.get(KEYS["name"]) or None,
        advisor=advisor or None,
        office=saved.get(KEYS["office"]) or None,
    )


async def save(session: AsyncSession, values: dict[str, str | None]) -> None:
    """Enregistre les champs donnés (et eux seuls) ; un champ vide est retiré (le conseiller vidé
    garde une marque vide, pour ne pas être pré-rempli à nouveau)."""
    for field, value in values.items():
        key = KEYS[field]
        text = (value or "").strip()
        if not text and field == "advisor":
            text = ""
        elif not text:
            await session.execute(delete(Setting).where(Setting.key == key))
            continue
        await session.execute(
            insert(Setting)
            .values(key=key, value=text)
            .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": text})
        )
