"""Ressources partagées par l'API, le worker et les commandes ponctuelles."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from jobbot.db.base import create_engine, create_sessionmaker
from jobbot.settings import Settings


@dataclass
class Runtime:
    settings: Settings
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]

    @classmethod
    def create(cls, settings: Settings) -> "Runtime":
        engine = create_engine(settings)
        return cls(settings=settings, engine=engine, sessionmaker=create_sessionmaker(engine))

    async def dispose(self) -> None:
        await self.engine.dispose()
