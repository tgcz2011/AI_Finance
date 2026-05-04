from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.core.enums import Currency, Market


@dataclass(frozen=True)
class Account:
    id: str
    ai_player_id: str
    currency: Currency
    balance: Decimal = Decimal("0")
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class Position:
    account_id: str
    symbol: str
    quantity: Decimal = Decimal("0")
    cost_price: Decimal = Decimal("0")
    market: Market = Market.A_STOCK
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def market_value(self) -> Decimal:
        return self.quantity * self.cost_price


@dataclass(frozen=True)
class Loan:
    account_id: str
    principal: Decimal = Decimal("0")
    interest_accrued: Decimal = Decimal("0")
    daily_rate: Decimal = Decimal("0.0005")
    is_active: bool = True
    disbursed_at: datetime = field(default_factory=datetime.now)

    @property
    def total_debt(self) -> Decimal:
        return self.principal + self.interest_accrued


@dataclass(frozen=True)
class AccountSummary:
    ai_player_id: str
    total_assets_cny: Decimal = Decimal("0")
    cash_by_currency: dict[str, Decimal] = field(default_factory=dict)
    positions: tuple[Position, ...] = ()
    total_debt: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    daily_pnl: Decimal = Decimal("0")

    @property
    def net_assets_cny(self) -> Decimal:
        return self.total_assets_cny - self.total_debt
