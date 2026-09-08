"""Singleton de conexão com o banco de dados.

Padrão Singleton: a engine e a session factory são criadas uma única vez e
reutilizadas em toda a aplicação, garantindo um único pool de conexões.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


class DatabaseSessionManager:
    """Gerencia a engine e a fábrica de sessões (Singleton)."""

    _engine: AsyncEngine | None = None
    _sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def __new__(cls) -> "DatabaseSessionManager":
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def init(self) -> None:
        """Inicializa a engine e a session factory (idempotente)."""
        if self._engine is not None:
            return
        self._engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self.init()
        assert self._engine is not None
        return self._engine

    @property
    def sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        if self._sessionmaker is None:
            self.init()
        assert self._sessionmaker is not None
        return self._sessionmaker

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None


db_manager = DatabaseSessionManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency que fornece uma sessão por request."""
    async with db_manager.sessionmaker() as session:
        yield session
