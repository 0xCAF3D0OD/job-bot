"""Ressources partagées par l'API, le worker et les commandes ponctuelles."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from jobbot.db.base import Access, create_engine, create_sessionmaker
from jobbot.settings import Settings
from jobbot.storage.base import Storage, create_storage


@dataclass
class Runtime:
    settings: Settings
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]
    storage: Storage

    @classmethod
    def create(cls, settings: Settings, access: Access = "app") -> "Runtime":
        """`access` : l'API (`app`), le worker, ou une commande du propriétaire (`admin`),
        chacun avec son accès à la base (docs/78 §3.1)."""
        engine = create_engine(settings, access)
        return cls(
            settings=settings,
            engine=engine,
            sessionmaker=create_sessionmaker(engine),
            storage=create_storage(settings),
        )

    async def dispose(self) -> None:
        await self.engine.dispose()
