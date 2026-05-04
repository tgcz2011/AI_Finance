from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from src.core.enums import Action, Market, MarketStatus, PriceLimitStatus
from src.core.constants import D, ZERO


@dataclass(frozen=True)
class TradeOrder:
    symbol: str
    action: Action
    quantity: Decimal
    price: Decimal = ZERO
    ai_player_id: str = ""
    timestamp: datetime | None = None


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    reason: str = ""
    adjusted_quantity: Decimal | None = None
