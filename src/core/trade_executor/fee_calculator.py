from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.core.constants import (
    A_STOCK_COMMISSION_BPS,
    A_STOCK_COMMISSION_MIN,
    A_STOCK_STAMP_TAX_BPS,
    CRYPTO_MAKER_FEE_BPS,
    CRYPTO_TAKER_FEE_BPS,
    DEFAULT_SLIPPAGE_BPS,
    US_STOCK_COMMISSION_BPS,
    ZERO,
    D,
)
from src.core.enums import Action, Market


@dataclass(frozen=True)
class FeeDetail:
    commission: Decimal = ZERO
    stamp_tax: Decimal = ZERO
    exchange_fee: Decimal = ZERO
    total_fee: Decimal = ZERO


class FeeCalculator:
    def __init__(
        self,
        a_stock_commission_bps: Decimal = A_STOCK_COMMISSION_BPS,
        a_stock_commission_min: Decimal = A_STOCK_COMMISSION_MIN,
        a_stock_stamp_tax_bps: Decimal = A_STOCK_STAMP_TAX_BPS,
        us_stock_commission_bps: Decimal = US_STOCK_COMMISSION_BPS,
        crypto_taker_fee_bps: Decimal = CRYPTO_TAKER_FEE_BPS,
        crypto_maker_fee_bps: Decimal = CRYPTO_MAKER_FEE_BPS,
    ) -> None:
        self._a_commission_bps = a_stock_commission_bps
        self._a_commission_min = a_stock_commission_min
        self._a_stamp_tax_bps = a_stock_stamp_tax_bps
        self._us_commission_bps = us_stock_commission_bps
        self._crypto_taker_bps = crypto_taker_fee_bps
        self._crypto_maker_bps = crypto_maker_fee_bps

    def calculate_fee(
        self,
        market: Market,
        action: Action,
        quantity: Decimal,
        price: Decimal,
        exchange_fee: Decimal = ZERO,
    ) -> FeeDetail:
        trade_value = quantity * price
        commission = ZERO
        stamp_tax = ZERO

        if market == Market.A_STOCK:
            commission = max(trade_value * self._a_commission_bps, self._a_commission_min)
            if action == Action.SELL:
                stamp_tax = trade_value * self._a_stamp_tax_bps
        elif market == Market.US_STOCK:
            commission = trade_value * self._us_commission_bps
        elif market == Market.CRYPTO:
            commission = trade_value * self._crypto_taker_bps

        total = commission + stamp_tax + exchange_fee
        return FeeDetail(
            commission=commission.quantize(D("0.00000001")),
            stamp_tax=stamp_tax.quantize(D("0.00000001")),
            exchange_fee=exchange_fee.quantize(D("0.00000001")),
            total_fee=total.quantize(D("0.00000001")),
        )


class SlippageCalculator:
    def __init__(self, slippage_bps: Decimal = DEFAULT_SLIPPAGE_BPS) -> None:
        self._slippage_bps = slippage_bps

    def calculate_execution_price(self, price: Decimal, action: Action) -> Decimal:
        if action == Action.BUY:
            return (price * (D("1") + self._slippage_bps)).quantize(D("0.00000001"))
        return (price * (D("1") - self._slippage_bps)).quantize(D("0.00000001"))

    def calculate_slippage_cost(self, price: Decimal, action: Action, quantity: Decimal) -> Decimal:
        exec_price = self.calculate_execution_price(price, action)
        return abs(exec_price - price) * quantity
