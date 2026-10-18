"""Démo publique (docs/72) : une installation à part, sans connexion, en lecture seule.

Le visiteur voit le compte fictif « demo », rempli par `jobbot demo-seed`. La base d'une démo
ne contient que ce compte et l'exploitant inerte créé avec lui : sinon, la plateforme refuse
de démarrer en mode démo, et la commande refuse de remplir la base.
"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts
from jobbot.db.models import User

DEMO_USERNAME = "demo"
MESSAGE = "Dans la démo, rien n'est enregistré."


class NotADemoDatabase(Exception):
    """La base contient un vrai compte : ce n'est pas une base de démo."""


async def check(session: AsyncSession) -> None:
    """Refuse une base qui contient un compte avec un mot de passe, ou un autre compte."""
    real = await session.scalar(
        select(User.username)
        .where(
            or_(
                User.password_hash != accounts.UNUSABLE_PASSWORD,
                User.username.not_in([DEMO_USERNAME, accounts.PLACEHOLDER_USERNAME]),
            )
        )
        .limit(1)
    )
    if real is not None:
        raise NotADemoDatabase(
            "cette base contient un vrai compte : le mode démo ne s'utilise que sur une base à part"
        )


async def account(session: AsyncSession) -> int | None:
    found = await session.scalar(select(User.id).where(User.username == DEMO_USERNAME))
    return None if found is None else int(found)
