from __future__ import annotations

from src.core.account.manager import AccountManager
from src.core.constants import A_STOCK_LOT_SIZE, ZERO, D
from src.core.enums import Action, Currency, Market, MarketStatus, PriceLimitStatus
from src.core.trade_validator.models import TradeOrder, ValidationResult


class TradeValidator:
    def __init__(self, account_manager: AccountManager) -> None:
        self._account_mgr = account_manager
        self._whitelist: dict[str, dict] = {}
        self._market_status: dict[str, MarketStatus] = {}
        self._price_limits: dict[str, PriceLimitStatus] = {}

    def set_whitelist(self, whitelist: dict[str, dict]) -> None:
        self._whitelist = whitelist

    def set_market_status(self, status_map: dict[str, MarketStatus]) -> None:
        self._market_status = status_map

    def set_price_limits(self, limits: dict[str, PriceLimitStatus]) -> None:
        self._price_limits = limits

    def validate(self, order: TradeOrder) -> ValidationResult:
        if order.action == Action.HOLD:
            return ValidationResult(is_valid=True)
        symbol_result = self.validate_symbol(order)
        if not symbol_result.is_valid:
            return symbol_result
        qty_result = self.validate_quantity(order)
        if not qty_result.is_valid:
            return qty_result
        market_result = self.validate_market_status(order)
        if not market_result.is_valid:
            return market_result
        limit_result = self.validate_price_limit(order)
        if not limit_result.is_valid:
            return limit_result
        if order.action == Action.BUY:
            funding_result = self.validate_funding(order)
            if not funding_result.is_valid:
                return funding_result
        elif order.action == Action.SELL:
            holding_result = self.validate_holding(order)
            if not holding_result.is_valid:
                return holding_result
        return ValidationResult(is_valid=True, adjusted_quantity=qty_result.adjusted_quantity)

    def validate_symbol(self, order: TradeOrder) -> ValidationResult:
        if order.symbol not in self._whitelist:
            return ValidationResult(is_valid=False, reason=f"Symbol {order.symbol} not in whitelist")
        return ValidationResult(is_valid=True)

    def validate_quantity(self, order: TradeOrder) -> ValidationResult:
        if order.quantity <= ZERO:
            return ValidationResult(is_valid=False, reason="Quantity must be positive")
        symbol_info = self._whitelist.get(order.symbol, {})
        market = symbol_info.get("market")
        min_qty = symbol_info.get("min_quantity", ZERO)
        precision = symbol_info.get("quantity_precision", 0)
        if market == Market.A_STOCK.value:
            lot_size = A_STOCK_LOT_SIZE
            adjusted = (int(order.quantity / lot_size)) * lot_size
            if adjusted <= 0:
                return ValidationResult(
                is_valid=False,
                reason=f"Quantity {order.quantity} below A-stock lot size {lot_size}",
            )
            return ValidationResult(is_valid=True, adjusted_quantity=D(adjusted))
        if market == Market.US_STOCK.value:
            adjusted = int(order.quantity)
            if adjusted <= 0:
                return ValidationResult(is_valid=False, reason="Quantity below US-stock minimum 1")
            return ValidationResult(is_valid=True, adjusted_quantity=D(adjusted))
        if market == Market.CRYPTO.value:
            quantize_str = D(10) ** (-precision)
            adjusted = order.quantity.quantize(quantize_str)
            if adjusted < min_qty:
                return ValidationResult(is_valid=False, reason=f"Quantity below crypto minimum {min_qty}")
            return ValidationResult(is_valid=True, adjusted_quantity=adjusted)
        return ValidationResult(is_valid=True, adjusted_quantity=order.quantity)

    def validate_market_status(self, order: TradeOrder) -> ValidationResult:
        status = self._market_status.get(order.symbol)
        if status == MarketStatus.HALTED:
            return ValidationResult(is_valid=False, reason=f"Symbol {order.symbol} is halted")
        if status == MarketStatus.CLOSED:
            return ValidationResult(is_valid=False, reason=f"Symbol {order.symbol} market is closed")
        return ValidationResult(is_valid=True)

    def validate_price_limit(self, order: TradeOrder) -> ValidationResult:
        limit = self._price_limits.get(order.symbol, PriceLimitStatus.NORMAL)
        if limit == PriceLimitStatus.LIMIT_UP and order.action == Action.BUY:
            return ValidationResult(is_valid=False, reason=f"Symbol {order.symbol} is at limit up, cannot buy")
        if limit == PriceLimitStatus.LIMIT_DOWN and order.action == Action.SELL:
            return ValidationResult(is_valid=False, reason=f"Symbol {order.symbol} is at limit down, cannot sell")
        return ValidationResult(is_valid=True)

    def validate_funding(self, order: TradeOrder) -> ValidationResult:
        symbol_info = self._whitelist.get(order.symbol, {})
        market = symbol_info.get("market")
        currency = Currency.CNY
        if market == Market.US_STOCK.value:
            currency = Currency.USD
        elif market == Market.CRYPTO.value:
            currency = Currency.USDT
        balance = self._account_mgr.get_balance(order.ai_player_id, currency)
        estimated_cost = order.quantity * order.price * D("1.002")
        if balance < estimated_cost:
            return ValidationResult(
            is_valid=False,
            reason=f"Insufficient {currency.value} balance: {balance} < {estimated_cost}",
        )
        return ValidationResult(is_valid=True)

    def validate_holding(self, order: TradeOrder) -> ValidationResult:
        pos = self._account_mgr.get_position(order.ai_player_id, order.symbol)
        available = pos.quantity if pos else ZERO
        if available < order.quantity:
            return ValidationResult(is_valid=False, reason=f"Insufficient holding: {available} < {order.quantity}")
        return ValidationResult(is_valid=True)
