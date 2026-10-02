from alembic import context
from sqlalchemy import create_engine, pool

from jobbot.db import models  # noqa: F401  (enregistre les tables)
from jobbot.db.base import Base

config = context.config


def run_migrations() -> None:
    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        raise RuntimeError("sqlalchemy.url absent de la configuration Alembic")
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("Le mode hors ligne n'est pas pris en charge : utiliser `jobbot migrate`.")
run_migrations()
