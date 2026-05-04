from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from src.core.enums import AlertLevel
from src.core.types.event_bus import EventBus, Event

logger = logging.getLogger(__name__)


class LogManager:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus
        self._log_buffer: list[dict] = []

    @staticmethod
    def mask_sensitive(value: str) -> str:
        if not value or len(value) <= 8:
            return "***"
        return value[:4] + "***" + value[-4:]

    def log_decision_request(self, ai_player_id: str, decisions: Any) -> None:
        self._append("DECISION_REQUEST", f"AI {ai_player_id} decisions", {"ai_player_id": ai_player_id})

    def log_interception(self, ai_player_id: str, symbol: str, reason: str) -> None:
        self._append("INTERCEPTION", f"AI {ai_player_id} symbol {symbol}: {reason}", {"ai_player_id": ai_player_id, "symbol": symbol, "reason": reason})

    def log_trade_execution(self, account_id: str, symbol: str, action: str, quantity: Any, price: Any) -> None:
        self._append("TRADE_EXECUTION", f"{action} {quantity} {symbol} @ {price}", {"account_id": account_id, "symbol": symbol})

    def log_interest(self, account_id: str, amount: Any) -> None:
        self._append("INTEREST", f"Interest {amount} for {account_id}", {"account_id": account_id})

    def log_exchange(self, account_id: str, from_c: str, to_c: str, amount: Any) -> None:
        self._append("EXCHANGE", f"Exchange {amount} {from_c}->{to_c}", {"account_id": account_id})

    def log_risk_event(self, ai_player_id: str, rule: str, details: str) -> None:
        self._append("RISK_EVENT", f"Risk {rule}: {details}", {"ai_player_id": ai_player_id, "rule": rule}, AlertLevel.WARNING)

    def _append(self, category: str, message: str, details: dict | None = None, level: AlertLevel = AlertLevel.INFO) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "category": category,
            "message": message,
            "details": details,
        }
        self._log_buffer.append(entry)
        if self._event_bus:
            self._event_bus.publish(Event(event_type="log_entry", payload=entry))
        log_method = getattr(logger, level.value.lower(), logger.info)
        log_method(f"[{category}] {message}")

    def get_recent_logs(self, count: int = 100) -> list[dict]:
        return self._log_buffer[-count:]
