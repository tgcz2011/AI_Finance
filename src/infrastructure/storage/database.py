from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class Database:
    def __init__(self, db_path: str | Path = "data/ai_finance.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_async_engine(
            f"sqlite+aiosqlite:///{self._db_path}",
            echo=False,
            pool_pre_ping=True,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        async with self._engine.begin() as conn:
            await conn.execute(self._text("PRAGMA journal_mode=WAL"))
            await conn.execute(self._text("PRAGMA synchronous=NORMAL"))
            await conn.execute(self._text("PRAGMA foreign_keys=ON"))
            from src.infrastructure.storage.models import Base
            await conn.run_sync(Base.metadata.create_all)
        self._initialized = True

    @staticmethod
    def _text(stmt: str):
        from sqlalchemy import text
        return text(stmt)

    async def close(self) -> None:
        await self._engine.dispose()
        self._initialized = False

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as sess:
            try:
                yield sess
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise
