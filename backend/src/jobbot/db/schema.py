"""Migrations Alembic : configuration, application et vérification de la révision.

Les migrations sont dans le paquet (jobbot/db/migrations) pour voyager avec lui.
Elles ne sont jamais appliquées au démarrage de l'API ou du worker : `jobbot migrate` seulement.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, create_engine, make_url, pool, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncConnection

from jobbot.db.base import APP_ROLE, WORKER_ROLE
from jobbot.settings import Settings

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def alembic_config(settings: Settings) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    # « % » doit être échappé dans les options Alembic (mots de passe encodés en URL).
    url = settings.url_for("admin")
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def head_revision() -> str | None:
    script = ScriptDirectory(str(MIGRATIONS_DIR))
    return script.get_current_head()


def upgrade(settings: Settings) -> None:
    command.upgrade(alembic_config(settings), "head")


def role_passwords(settings: Settings) -> dict[str, str]:
    """Les mots de passe des rôles de l'API et du worker, tirés de leur adresse de connexion."""
    wanted: dict[str, str] = {}
    for access, role in (("app", APP_ROLE), ("worker", WORKER_ROLE)):
        url = make_url(settings.url_for(access))
        if url.username == role and url.password:
            wanted[role] = str(url.password)
    return wanted


def set_role_password(conn: Connection, role: str, password: str) -> None:
    # Le mot de passe passe par un réglage de la transaction : jamais dans le texte d'une
    # requête, donc jamais dans un journal du serveur.
    conn.execute(text("select set_config('jobbot.role_password', :p, true)"), {"p": password})
    conn.execute(
        text(
            "do $$ begin execute format('alter role %I password %L', "
            f"'{role}', current_setting('jobbot.role_password')); end $$"
        )
    )


def sync_role_passwords(settings: Settings) -> list[str]:
    """Donne aux rôles de l'API et du worker le mot de passe de leur adresse de connexion
    (docs/78 §3.1), s'il y en a un : une seule source, le fichier de réglages. Sans mot de
    passe (connexion locale de confiance), rien ne change."""
    wanted = role_passwords(settings)
    if not wanted:
        return []
    engine = create_engine(settings.url_for("admin"), poolclass=pool.NullPool)
    try:
        with engine.begin() as conn:
            for role, password in wanted.items():
                set_role_password(conn, role, password)
    finally:
        engine.dispose()
    return list(wanted)


async def current_revision(conn: AsyncConnection) -> str | None:
    try:
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
    except ProgrammingError:
        # Table absente : aucune migration appliquée.
        await conn.rollback()
        return None
    return result.scalar_one_or_none()
