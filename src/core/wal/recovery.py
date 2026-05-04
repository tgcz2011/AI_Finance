from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import Callable

from src.core.types.result import Err, Ok, Result
from src.core.wal.manager import WALManager

logger = logging.getLogger(__name__)


class SystemRecovery:
    def __init__(self, wal_manager: WALManager | None = None) -> None:
        self._wal_manager = wal_manager
        self._shutdown_requested = False
        self._on_shutdown: list[Callable] = []

    def register_shutdown_handler(self, handler: Callable) -> None:
        self._on_shutdown.append(handler)

    async def recover_on_startup(self) -> Result[None]:
        if self._wal_manager is None:
            return Ok(None)
        try:
            uncommitted = await self._wal_manager.scan_uncommitted()
            for entry in uncommitted:
                is_valid = await self._wal_manager.verify_checksum(entry)
                if is_valid:
                    await self._wal_manager.rollback(entry.id)
                    logger.info(f"Rolled back uncommitted WAL entry {entry.id}")
                else:
                    logger.error(f"Corrupted WAL entry {entry.id}, checksum mismatch")

            committed = await self._wal_manager.scan_committed_unpersisted()
            for entry in committed:
                is_valid = await self._wal_manager.verify_checksum(entry)
                if not is_valid:
                    logger.error(f"Corrupted committed WAL entry {entry.id}")

            return Ok(None)
        except Exception as e:
            return Err(f"Recovery failed: {e}")

    async def graceful_shutdown(self) -> None:
        self._shutdown_requested = True
        logger.info("Graceful shutdown initiated")
        for handler in self._on_shutdown:
            try:
                result = handler()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Shutdown handler error: {e}")
        logger.info("Graceful shutdown completed")

    def setup_signal_handlers(self) -> None:
        def _signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, requesting graceful shutdown")
            self._shutdown_requested = True

        try:
            signal.signal(signal.SIGINT, _signal_handler)
            signal.signal(signal.SIGTERM, _signal_handler)
        except ValueError:
            pass

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested
