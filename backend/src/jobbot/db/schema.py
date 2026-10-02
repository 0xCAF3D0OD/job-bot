"""Migrations Alembic : configuration, application et vérification de la révision.

Les migrations sont dans le paquet (jobbot/db/migrations) pour voyager avec lui.
Elles ne sont jamais appliquées au démarrage de l'API ou du worker : `jobbot migrate` seulement.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncConnection

from jobbot.settings import Settings

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def alembic_config(settings: Settings) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    # « % » doit être échappé dans les options Alembic (mots de passe encodés en URL).
    config.set_main_option("sqlalchemy.url", settings.sqlalchemy_url.replace("%", "%%"))
    return config


def head_revision() -> str | None:
    script = ScriptDirectory(str(MIGRATIONS_DIR))
    return script.get_current_head()


def upgrade(settings: Settings) -> None:
    command.upgrade(alembic_config(settings), "head")


async def current_revision(conn: AsyncConnection) -> str | None:
    try:
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
    except ProgrammingError:
        # Table absente : aucune migration appliquée.
        await conn.rollback()
        return None
    return result.scalar_one_or_none()
