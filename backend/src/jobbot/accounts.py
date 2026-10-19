"""Le compte en cours (docs/65 §7) : chaque lecture et écriture appartient à un compte.

Le compte est porté par une variable de contexte, posée par la connexion (API), par la tâche
de fond (un passage par compte) ou par la commande. Au début de chaque transaction, la base
reçoit ce compte (`app.user_id`) ; ses règles de sécurité au niveau des lignes ne laissent
alors voir et écrire que les lignes de ce compte, et une ligne créée lui est rattachée
d'office. Sans compte, la base ne montre rien et refuse toute écriture : on échoue fermé.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jobbot.db.base import ACCOUNT as _CURRENT
from jobbot.db.base import WORKER_ROLE
from jobbot.db.models import User

# Compte créé quand la base n'en a aucun (installation neuve, tests) : son mot de passe ne
# correspond à rien, `jobbot set-password` lui donne son identifiant et son mot de passe.
PLACEHOLDER_USERNAME = "proprietaire"
UNUSABLE_PASSWORD = "!"


def current() -> int | None:
    return _CURRENT.get()


def set_current(user_id: int | None) -> None:
    """Pose le compte pour la suite de la tâche en cours (requête, commande)."""
    _CURRENT.set(user_id)


@contextmanager
def use(user_id: int | None) -> Iterator[None]:
    """Le temps d'un bloc, tout se fait au nom de ce compte."""
    token = _CURRENT.set(user_id)
    try:
        yield
    finally:
        _CURRENT.reset(token)


async def owner_id(session: AsyncSession) -> int:
    """Le compte de l'exploitant : le premier créé. Il reçoit ce qui n'est pas encore
    rangé par compte (la boîte e-mail de l'installation, ses notifications)."""
    # La base le dit à tout compte, sans montrer la liste des comptes (migration 0054).
    found = await session.scalar(select(func.platform_owner()))
    if found is not None:
        return int(found)
    user = User(username=PLACEHOLDER_USERNAME, password_hash=UNUSABLE_PASSWORD)
    session.add(user)
    await session.flush()
    return user.id


async def account_ids(session: AsyncSession) -> list[int]:
    """Les comptes pour qui tournent les tâches : un compte suspendu n'en a plus."""
    rows = await session.scalars(select(func.active_accounts()))
    return [int(i) for i in rows]


async def is_owner(session: AsyncSession) -> bool:
    return current() == await owner_id(session)


async def writes_shared(session: AsyncSession) -> bool:
    """Les tables communes (entreprises, logos, actualités…) ne sont écrites que par le worker
    et l'exploitant (docs/78 §3.2) : ce qu'un invité trouve reste dans ses offres."""
    if await is_owner(session):
        return True
    return bool(
        await session.scalar(text(f"select pg_has_role(current_user, '{WORKER_ROLE}', 'usage')"))
    )


async def account_of_token(session: AsyncSession, kind: str, digest: str) -> int | None:
    """Le compte d'un jeton (extension ou agenda), cherché avant que le compte soit connu ;
    la base ne rend que ce numéro (fonctions des migrations 0046, 0053 et 0056)."""
    function = {"extension": "account_of_extension_token", "calendar": "account_of_calendar_token"}
    found = await session.scalar(select(getattr(func, function[kind])(digest)))
    return None if found is None else int(found)


async def account_of_session(session: AsyncSession, digest: str) -> int | None:
    """Le compte d'une session (compte non suspendu), cherché avant que le compte soit connu
    (migration 0054) ; son expiration est vérifiée ensuite, en son nom."""
    found = await session.scalar(select(func.account_of_session(digest)))
    return None if found is None else int(found)


async def account_of_login(session: AsyncSession, username: str) -> int | None:
    """Le compte de cet identifiant (sans tenir compte des majuscules), ou None."""
    found = await session.scalar(select(func.account_of_login(username)))
    return None if found is None else int(found)


async def has_password(session: AsyncSession) -> bool:
    """La plateforme a déjà un compte avec mot de passe : sinon, premier démarrage."""
    return bool(await session.scalar(select(func.platform_has_password())))


async def act_as_owner(sessionmaker: async_sessionmaker[AsyncSession]) -> int:
    """Commandes ponctuelles (`jobbot reparse`…) : au nom de l'exploitant."""
    async with sessionmaker.begin() as session:
        owner = await owner_id(session)
    set_current(owner)
    return owner
