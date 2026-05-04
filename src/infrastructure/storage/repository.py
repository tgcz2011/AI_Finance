from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class Repository(Generic[T]):
    def __init__(self, session: AsyncSession, model_class: type[T]) -> None:
        self._session = session
        self._model_class = model_class

    async def get_by_id(self, id_val: Any) -> T | None:
        return await self._session.get(self._model_class, id_val)

    async def get_all(self) -> Sequence[T]:
        stmt = select(self._model_class)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def add_all(self, entities: list[T]) -> list[T]:
        self._session.add_all(entities)
        await self._session.flush()
        return entities

    async def update(self, entity: T) -> T:
        await self._session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        await self._session.delete(entity)
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    @property
    def session(self) -> AsyncSession:
        return self._session
