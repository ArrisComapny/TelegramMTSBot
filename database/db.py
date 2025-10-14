from typing import AsyncIterator, Optional
from contextlib import asynccontextmanager

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from config import USER, PASS, HOST, PORT, BASE

metadata = MetaData()

class Base(DeclarativeBase):
    metadata = metadata

class Database:
    """Инкапсулирует engine и фабрику сессий."""
    def __init__(self):
        self._dsn = f"postgresql+asyncpg://{USER}:{PASS}@{HOST}:{PORT}/{BASE}"
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def connect(self) -> None:
        if self.engine:
            return
        self.engine = create_async_engine(self._dsn,
                                          pool_pre_ping=True,
                                          pool_size=5,
                                          max_overflow=10,
                                          pool_recycle=1800,
                                          echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def disconnect(self) -> None:
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Контекстный менеджер сессии."""
        if not self.session_factory:
            raise RuntimeError("Database is not connected. Call connect() first.")
        session: AsyncSession = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
