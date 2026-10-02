"""Ressources partagées par l'API, le worker et les commandes ponctuelles."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from jobbot.db.base import create_engine, create_sessionmaker
from jobbot.settings import Settings
from jobbot.storage.base import Storage, create_storage


@dataclass
class Runtime:
    settings: Settings
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]
    storage: Storage

    @classmethod
    def create(cls, settings: Settings) -> "Runtime":
        engine = create_engine(settings)
        return cls(
            settings=settings,
            engine=engine,
            sessionmaker=create_sessionmaker(engine),
            storage=create_storage(settings),
        )

    async def dispose(self) -> None:
        await self.engine.dispose()
