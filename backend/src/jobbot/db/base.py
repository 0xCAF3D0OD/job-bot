"""Moteur et sessions SQLAlchemy (asynchrones, pilote psycopg 3)."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import partial
from typing import Any, Literal

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from jobbot.settings import Settings

# Rôles sans privilège particulier (docs/65 §7, docs/78 §3.1) : les règles de sécurité au niveau
# des lignes s'appliquent à eux, alors qu'un superutilisateur ou le propriétaire des tables les
# contourne. L'API se connecte en jobbot_app ; le worker en jobbot_worker, qui écrit aussi les
# tables communes ; les commandes du propriétaire (`migrate`, `demo-seed`, `set-password`) avec
# l'utilisateur des migrations, sans restriction.
APP_ROLE = "jobbot_app"
WORKER_ROLE = "jobbot_worker"
Access = Literal["app", "worker", "admin"]
RESTRICTED = (APP_ROLE, WORKER_ROLE)
# Le compte en cours (voir jobbot.accounts), transmis à la base au début de chaque transaction.
ACCOUNT: ContextVar[int | None] = ContextVar("jobbot_account", default=None)
# Démo publique (docs/76 §1) : les requêtes d'un visiteur ne peuvent rien écrire en base, même
# une lecture qui enregistrerait quelque chose en passant.
READ_ONLY: ContextVar[bool] = ContextVar("jobbot_read_only", default=False)


@contextmanager
def read_only() -> Iterator[None]:
    token = READ_ONLY.set(True)
    try:
        yield
    finally:
        READ_ONLY.reset(token)


class Base(DeclarativeBase):
    pass


def _on_connect(dbapi_connection: Any, _record: Any, access: Access = "app") -> None:
    if access == "admin":
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("select current_user")
        row = cursor.fetchone()
        if row is not None and row[0] in RESTRICTED:
            # Connecté directement avec un rôle restreint : rien à faire, et rien à défaire.
            return
        # Connecté en administrateur (ancienne configuration, docs/78 §3.1) : on se restreint
        # soi-même ; la plateforme le signale à l'exploitant.
        for role in (WORKER_ROLE, APP_ROLE) if access == "worker" else (APP_ROLE,):
            cursor.execute("select 1 from pg_roles where rolname = %s", (role,))
            if cursor.fetchone() is not None:
                cursor.execute(f"set role {role}")
                break
        else:
            # Sans ce rôle, la séparation des comptes serait contournée sans bruit (docs/69 §1).
            # Une base pas encore migrée n'a ni le rôle ni les règles : elle reste joignable
            # (l'état dit qu'elle est à mettre à jour) ; une base qui a les règles, non.
            cursor.execute("select 1 from pg_policies where policyname = 'account_isolation'")
            if cursor.fetchone() is not None:
                raise RuntimeError(
                    f"rôle {APP_ROLE} absent : la séparation des comptes ne s'appliquerait pas"
                )
    finally:
        cursor.close()
        dbapi_connection.commit()


def _on_begin(connection: Any) -> None:
    if READ_ONLY.get():
        # Avant toute autre instruction de la transaction.
        connection.exec_driver_sql("set transaction read only")
    account = ACCOUNT.get()
    connection.exec_driver_sql(
        "select set_config('app.user_id', %s, true)",
        ("" if account is None else str(account),),
    )


def create_engine(settings: Settings, access: Access = "app") -> AsyncEngine:
    # Aucune connexion n'est ouverte ici : l'application démarre même si la base est absente.
    engine = create_async_engine(
        settings.url_for(access),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )
    event.listen(engine.sync_engine, "connect", partial(_on_connect, access=access))
    event.listen(engine.sync_engine, "begin", _on_begin)
    return engine


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def connected_as_admin(session: AsyncSession) -> bool:
    """La connexion s'est faite avec un rôle qui passe outre la séparation des comptes
    (superutilisateur ou BYPASSRLS), même s'il s'est restreint ensuite (docs/78 §3.1)."""
    found = await session.scalar(
        text("select rolsuper or rolbypassrls from pg_roles where rolname = session_user")
    )
    return bool(found)
