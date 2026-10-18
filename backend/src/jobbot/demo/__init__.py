"""Démo publique (docs/72) : une installation à part, sans connexion, en lecture seule.

Le visiteur voit le compte fictif « demo », rempli par `jobbot demo-seed`. La base d'une démo
ne contient que ce compte et l'exploitant inerte créé avec lui, sans aucune donnée : sinon, la
plateforme refuse de démarrer en mode démo, et la commande refuse de remplir la base.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jobbot import accounts
from jobbot.db.models import Application, Document, Offer, ProfileChunk, User

DEMO_USERNAME = "demo"
MESSAGE = "Dans la démo, rien n'est enregistré."


class NotADemoDatabase(Exception):
    """La base contient un vrai compte : ce n'est pas une base de démo."""


async def check(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    """Refuse une base qui contient un compte avec un mot de passe, un autre compte, ou des
    données hors du compte fictif.

    Une installation neuve, ou sans connexion, a un exploitant sans mot de passe : seuls ses
    données le distinguent d'une base de démo (docs/76 §1). Chaque compte se lit à son nom,
    les règles de la base ne montrant que les lignes du compte en cours.
    """
    async with sessionmaker() as session:
        users = (await session.execute(select(User.id, User.username, User.password_hash))).all()
    for user_id, username, password_hash in users:
        if password_hash != accounts.UNUSABLE_PASSWORD or username not in (
            DEMO_USERNAME,
            accounts.PLACEHOLDER_USERNAME,
        ):
            raise NotADemoDatabase(
                "cette base contient un vrai compte : le mode démo ne s'utilise que sur une base "
                "à part"
            )
        if username == DEMO_USERNAME:
            continue
        with accounts.use(user_id):
            async with sessionmaker() as session:
                for model in (Offer, Application, Document, ProfileChunk):
                    if await session.scalar(select(model.id).limit(1)) is not None:
                        raise NotADemoDatabase(
                            "cette base contient des données hors de la démo : le mode démo ne "
                            "s'utilise que sur une base à part"
                        )


async def account(session: AsyncSession) -> int | None:
    found = await session.scalar(select(User.id).where(User.username == DEMO_USERNAME))
    return None if found is None else int(found)
