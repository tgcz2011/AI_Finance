from __future__ import annotations

from src.core.types.event_bus import EventBus, Event
from src.core.enums import AlertLevel


class StateIntegrityChecker:
    def __init__(self, event_bus: EventBus, check_interval_seconds: int = 600) -> None:
        self._event_bus = event_bus
        self._check_interval = check_interval_seconds
        self._last_check_passed = True

    def check_balance_integrity(self, accounts: list, positions: list, loans: list) -> bool:
        total_cash = sum(a.balance for a in accounts)
        total_position_value = sum(p.quantity * p.cost_price for p in positions)
        total_debt = sum(l.principal + l.interest_accrued for l in loans if l.is_active)
        net_assets = total_cash + total_position_value - total_debt
        passed = net_assets >= 0
        if not passed:
            self._event_bus.publish(Event(
                event_type="integrity_check_failed",
                payload={"type": "balance", "net_assets": float(net_assets)},
            ))
        return passed

    def check_position_consistency(self, positions: list) -> bool:
        passed = all(p.quantity >= 0 and p.cost_price >= 0 for p in positions)
        if not passed:
            self._event_bus.publish(Event(
                event_type="integrity_check_failed",
                payload={"type": "position_consistency"},
            ))
        return passed

    @property
    def last_check_passed(self) -> bool:
        return self._last_check_passed

    @property
    def check_interval_seconds(self) -> int:
        return self._check_interval
