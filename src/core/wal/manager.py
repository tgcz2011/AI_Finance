from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import WALStatus, OperationType
from src.core.types.result import Ok, Err, Result
from src.infrastructure.storage.models import WALLogORM


class WALManager:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _compute_checksum(params: dict[str, Any]) -> str:
        raw = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def begin(self, operation_type: OperationType, params: dict[str, Any]) -> Result[int]:
        try:
            checksum = self._compute_checksum(params)
            wal_entry = WALLogORM(
                operation_type=operation_type.value,
                status=WALStatus.PENDING.value,
                params_json=json.dumps(params, default=str),
                checksum=checksum,
            )
            self._session.add(wal_entry)
            await self._session.flush()
            return Ok(wal_entry.id)
        except Exception as e:
            return Err(f"WAL begin failed: {e}")

    async def commit(self, wal_id: int) -> Result[None]:
        try:
            stmt = (
                update(WALLogORM)
                .where(WALLogORM.id == wal_id)
                .values(status=WALStatus.COMMITTED.value, committed_at=datetime.now())
            )
            await self._session.execute(stmt)
            await self._session.flush()
            return Ok(None)
        except Exception as e:
            return Err(f"WAL commit failed: {e}")

    async def rollback(self, wal_id: int) -> Result[None]:
        try:
            stmt = (
                update(WALLogORM)
                .where(WALLogORM.id == wal_id)
                .values(status=WALStatus.ROLLED_BACK.value)
            )
            await self._session.execute(stmt)
            await self._session.flush()
            return Ok(None)
        except Exception as e:
            return Err(f"WAL rollback failed: {e}")

    async def scan_uncommitted(self) -> list[WALLogORM]:
        stmt = select(WALLogORM).where(
            WALLogORM.status == WALStatus.PENDING.value
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def scan_committed_unpersisted(self) -> list[WALLogORM]:
        stmt = select(WALLogORM).where(
            WALLogORM.status == WALStatus.COMMITTED.value
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def verify_checksum(self, wal_entry: WALLogORM) -> bool:
        try:
            params = json.loads(wal_entry.params_json)
            expected = self._compute_checksum(params)
            return expected == wal_entry.checksum
        except Exception:
            return False
