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
    données le distinguent d'une base de démo (docs/76 §1). Les comptes se lisent au nom de
    l'exploitant, les données de chacun au sien.
    """
    async with sessionmaker.begin() as session:
        owner = await accounts.owner_id(session)
    # L'exploitant voit tous les comptes (migration 0054).
    with accounts.use(owner):
        async with sessionmaker() as session:
            users = (
                await session.execute(select(User.id, User.username, User.password_hash))
            ).all()
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
                    # Filtré aussi à la main : la commande du propriétaire passe outre les règles.
                    query = select(model.id).where(model.user_id == user_id).limit(1)
                    if await session.scalar(query) is not None:
                        raise NotADemoDatabase(
                            "cette base contient des données hors de la démo : le mode démo ne "
                            "s'utilise que sur une base à part"
                        )


async def account(session: AsyncSession) -> int | None:
    return await accounts.account_of_login(session, DEMO_USERNAME)
