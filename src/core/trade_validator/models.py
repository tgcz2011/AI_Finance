from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.core.constants import ZERO
from src.core.enums import Action


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
