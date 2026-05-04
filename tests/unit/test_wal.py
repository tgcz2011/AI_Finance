import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.core.enums import OperationType, WALStatus
from src.core.wal.manager import WALManager
from src.core.wal.recovery import SystemRecovery
from src.core.wal.integrity import StateIntegrityChecker
from src.core.types.event_bus import EventBus, Event
from src.infrastructure.storage.models import WALLogORM


class TestWALManager:
    def test_compute_checksum_deterministic(self):
        c1 = WALManager._compute_checksum({"symbol": "AAPL", "qty": 100})
        c2 = WALManager._compute_checksum({"symbol": "AAPL", "qty": 100})
        assert c1 == c2

    def test_compute_checksum_different_params(self):
        c1 = WALManager._compute_checksum({"symbol": "AAPL"})
        c2 = WALManager._compute_checksum({"symbol": "GOOG"})
        assert c1 != c2

    def test_compute_checksum_order_independent(self):
        c1 = WALManager._compute_checksum({"a": 1, "b": 2})
        c2 = WALManager._compute_checksum({"b": 2, "a": 1})
        assert c1 == c2


class TestSystemRecovery:
    def test_shutdown_requested_default_false(self):
        recovery = SystemRecovery()
        assert recovery.shutdown_requested is False

    def test_register_shutdown_handler(self):
        recovery = SystemRecovery()
        called = []
        recovery.register_shutdown_handler(lambda: called.append(1))
        assert len(recovery._on_shutdown) == 1

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        recovery = SystemRecovery()
        called = []
        recovery.register_shutdown_handler(lambda: called.append(1))
        await recovery.graceful_shutdown()
        assert recovery.shutdown_requested is True
        assert called == [1]

    @pytest.mark.asyncio
    async def test_recover_no_wal_manager(self):
        recovery = SystemRecovery()
        result = await recovery.recover_on_startup()
        assert result.is_ok


class TestStateIntegrityChecker:
    def test_balance_integrity_pass(self):
        bus = EventBus()
        checker = StateIntegrityChecker(bus)
        account = MagicMock()
        account.balance = 1000000
        result = checker.check_balance_integrity([account], [], [])
        assert result is True

    def test_balance_integrity_fail_negative(self):
        bus = EventBus()
        checker = StateIntegrityChecker(bus)
        account = MagicMock()
        account.balance = -100
        result = checker.check_balance_integrity([account], [], [])
        assert result is False

    def test_position_consistency_pass(self):
        bus = EventBus()
        checker = StateIntegrityChecker(bus)
        pos = MagicMock()
        pos.quantity = 100
        pos.cost_price = 50
        result = checker.check_position_consistency([pos])
        assert result is True

    def test_position_consistency_fail_negative_qty(self):
        bus = EventBus()
        checker = StateIntegrityChecker(bus)
        pos = MagicMock()
        pos.quantity = -10
        pos.cost_price = 50
        result = checker.check_position_consistency([pos])
        assert result is False
