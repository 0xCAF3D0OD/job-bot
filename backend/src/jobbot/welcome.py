"""L'accueil après la première connexion (docs/66) : où en est le compte.

L'avancement est un réglage du compte (`welcome`) : l'écran atteint, l'objectif choisi au
premier écran, le métier. Sans ce réglage, le compte est nouveau : l'accueil l'attend.
L'exploitant ne le voit jamais.
"""

from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts
from jobbot.db.models import Setting
from jobbot.profiles.service import main_profile

KEY = "welcome"
Status = Literal["pending", "postponed", "done"]


async def state(session: AsyncSession) -> dict[str, Any]:
    if await accounts.is_owner(session):
        return {"done": True}
    value = await session.scalar(select(Setting.value).where(Setting.key == KEY))
    return value if isinstance(value, dict) else {}


def status(value: dict[str, Any]) -> Status:
    if value.get("done"):
        return "done"
    return "postponed" if value.get("postponed") else "pending"


async def save(session: AsyncSession, changes: dict[str, Any]) -> dict[str, Any]:
    # Fusion faite par la base (jsonb ||) : deux enregistrements rapprochés de l'accueil ne
    # s'écrasent pas l'un l'autre.
    statement = insert(Setting).values(key=KEY, value=changes)
    value = await session.scalar(
        statement.on_conflict_do_update(
            index_elements=["user_id", "key"],
            set_={"value": Setting.value.op("||")(statement.excluded.value)},
        ).returning(Setting.value)
    )
    trade = changes.get("trade")
    if isinstance(trade, str) and trade.strip():
        # Le métier devient le premier mot de « Mon domaine » : les Actualités le suivent, et
        # la page Alertes propose la recherche qui va avec.
        profile = await main_profile(session)
        preferences = dict(profile.preferences or {})
        words = [w for w in preferences.get("domain_keywords") or [] if isinstance(w, str)]
        name = trade.strip()
        preferences["domain_keywords"] = [name] + [w for w in words if w.lower() != name.lower()]
        profile.preferences = preferences
    return value if isinstance(value, dict) else {}
