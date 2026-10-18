"""Moteur et sessions SQLAlchemy (asynchrones, pilote psycopg 3)."""

from contextvars import ContextVar
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from jobbot.settings import Settings

# Rôle sans privilège particulier, créé par la migration des comptes (docs/65 §7) : les règles
# de sécurité au niveau des lignes s'appliquent à lui, alors qu'un superutilisateur ou le
# propriétaire des tables les contourne.
APP_ROLE = "jobbot_app"
# Le compte en cours (voir jobbot.accounts), transmis à la base au début de chaque transaction.
ACCOUNT: ContextVar[int | None] = ContextVar("jobbot_account", default=None)


class Base(DeclarativeBase):
    pass


def _on_connect(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("select 1 from pg_roles where rolname = %s", (APP_ROLE,))
        if cursor.fetchone() is not None:
            cursor.execute(f"set role {APP_ROLE}")
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
    account = ACCOUNT.get()
    connection.exec_driver_sql(
        "select set_config('app.user_id', %s, true)",
        ("" if account is None else str(account),),
    )


def create_engine(settings: Settings) -> AsyncEngine:
    # Aucune connexion n'est ouverte ici : l'application démarre même si la base est absente.
    engine = create_async_engine(
        settings.sqlalchemy_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )
    event.listen(engine.sync_engine, "connect", _on_connect)
    event.listen(engine.sync_engine, "begin", _on_begin)
    return engine


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
