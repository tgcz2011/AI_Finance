from __future__ import annotations

from decimal import Decimal

from src.core.account.models import Account, AccountSummary, Position
from src.core.constants import DEFAULT_SPREAD_BPS, ZERO, D
from src.core.enums import Currency, Market
from src.core.types.result import Err, Ok, Result


class AccountManager:
    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}
        self._positions: dict[str, dict[str, Position]] = {}
        self._exchange_rates: dict[tuple[str, str], dict[str, Decimal]] = {}
        self._spread_bps: Decimal = DEFAULT_SPREAD_BPS

    def create_account(self, ai_player_id: str, currency: Currency, initial_balance: Decimal = ZERO) -> Result[Account]:
        account_id = f"{ai_player_id}_{currency.value}"
        if account_id in self._accounts:
            return Err(f"Account {account_id} already exists")
        account = Account(
            id=account_id,
            ai_player_id=ai_player_id,
            currency=currency,
            balance=initial_balance,
        )
        self._accounts[account_id] = account
        if ai_player_id not in self._positions:
            self._positions[ai_player_id] = {}
        return Ok(account)

    def get_balance(self, ai_player_id: str, currency: Currency) -> Decimal:
        account_id = f"{ai_player_id}_{currency.value}"
        account = self._accounts.get(account_id)
        return account.balance if account else ZERO

    def get_account(self, ai_player_id: str, currency: Currency) -> Account | None:
        return self._accounts.get(f"{ai_player_id}_{currency.value}")

    def debit_cash(self, ai_player_id: str, currency: Currency, amount: Decimal) -> Result[Account]:
        if amount <= ZERO:
            return Err("Debit amount must be positive")
        account_id = f"{ai_player_id}_{currency.value}"
        account = self._accounts.get(account_id)
        if account is None:
            return Err(f"Account {account_id} not found")
        if account.balance < amount:
            return Err(f"Insufficient balance: {account.balance} < {amount}")
        new_account = Account(
            id=account.id,
            ai_player_id=account.ai_player_id,
            currency=account.currency,
            balance=account.balance - amount,
        )
        self._accounts[account_id] = new_account
        return Ok(new_account)

    def credit_cash(self, ai_player_id: str, currency: Currency, amount: Decimal) -> Result[Account]:
        if amount <= ZERO:
            return Err("Credit amount must be positive")
        account_id = f"{ai_player_id}_{currency.value}"
        account = self._accounts.get(account_id)
        if account is None:
            return Err(f"Account {account_id} not found")
        new_account = Account(
            id=account.id,
            ai_player_id=account.ai_player_id,
            currency=account.currency,
            balance=account.balance + amount,
        )
        self._accounts[account_id] = new_account
        return Ok(new_account)

    def exchange_currency(
        self,
        ai_player_id: str,
        from_currency: Currency,
        to_currency: Currency,
        amount: Decimal,
    ) -> Result[Decimal]:
        if from_currency == to_currency:
            return Ok(amount)
        if amount <= ZERO:
            return Err("Exchange amount must be positive")

        from_balance = self.get_balance(ai_player_id, from_currency)
        if from_balance < amount:
            return Err(f"Insufficient {from_currency.value} balance for exchange")

        rate_key = (from_currency.value, to_currency.value)
        rates = self._exchange_rates.get(rate_key)
        if rates is None:
            return Err(f"No exchange rate for {rate_key}")

        sell_rate = rates["sell_rate"]
        spread_multiplier = D("1") + self._spread_bps
        effective_rate = sell_rate * spread_multiplier
        received = amount * effective_rate

        debit_result = self.debit_cash(ai_player_id, from_currency, amount)
        if debit_result.is_err:
            return Err(debit_result.error)

        credit_result = self.credit_cash(ai_player_id, to_currency, received.quantize(D("0.00000001")))
        if credit_result.is_err:
            self.credit_cash(ai_player_id, from_currency, amount)
            return Err(credit_result.error)

        return Ok(received.quantize(D("0.00000001")))

    def set_exchange_rate(
        self,
        from_currency: Currency,
        to_currency: Currency,
        mid_rate: Decimal,
        buy_rate: Decimal,
        sell_rate: Decimal,
    ) -> None:
        self._exchange_rates[(from_currency.value, to_currency.value)] = {
            "mid_rate": mid_rate,
            "buy_rate": buy_rate,
            "sell_rate": sell_rate,
        }

    def get_position(self, ai_player_id: str, symbol: str) -> Position | None:
        return self._positions.get(ai_player_id, {}).get(symbol)

    def get_all_positions(self, ai_player_id: str) -> list[Position]:
        return list(self._positions.get(ai_player_id, {}).values())

    def add_position(
        self,
        ai_player_id: str,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        market: Market,
    ) -> Result[Position]:
        if quantity <= ZERO or price <= ZERO:
            return Err("Quantity and price must be positive")
        positions = self._positions.setdefault(ai_player_id, {})
        existing = positions.get(symbol)
        if existing:
            new_qty = existing.quantity + quantity
            new_cost = (existing.quantity * existing.cost_price + quantity * price) / new_qty
            pos = Position(
                account_id=f"{ai_player_id}_CNY",
                symbol=symbol,
                quantity=new_qty,
                cost_price=new_cost.quantize(D("0.00000001")),
                market=market,
            )
        else:
            pos = Position(
                account_id=f"{ai_player_id}_CNY",
                symbol=symbol,
                quantity=quantity,
                cost_price=price,
                market=market,
            )
        positions[symbol] = pos
        return Ok(pos)

    def reduce_position(
        self,
        ai_player_id: str,
        symbol: str,
        quantity: Decimal,
    ) -> Result[tuple[Decimal, Decimal]]:
        if quantity <= ZERO:
            return Err("Quantity must be positive")
        positions = self._positions.get(ai_player_id, {})
        existing = positions.get(symbol)
        if existing is None or existing.quantity < quantity:
            return Err(f"Insufficient position: {existing.quantity if existing else ZERO} < {quantity}")
        sell_avg_cost = existing.cost_price
        new_qty = existing.quantity - quantity
        if new_qty == ZERO:
            del positions[symbol]
        else:
            positions[symbol] = Position(
                account_id=existing.account_id,
                symbol=symbol,
                quantity=new_qty,
                cost_price=existing.cost_price,
                market=existing.market,
            )
        return Ok((sell_avg_cost, quantity * sell_avg_cost))

    def apply_dividend(self, ai_player_id: str, symbol: str, dividend_per_share: Decimal) -> Result[Decimal]:
        pos = self.get_position(ai_player_id, symbol)
        if pos is None:
            return Err(f"No position for {symbol}")
        total_dividend = pos.quantity * dividend_per_share
        credit_result = self.credit_cash(ai_player_id, Currency.CNY, total_dividend)
        if credit_result.is_err:
            return Err(credit_result.error)
        return Ok(total_dividend)

    def apply_ex_rights(
        self,
        ai_player_id: str,
        symbol: str,
        quantity_factor: Decimal,
        price_factor: Decimal,
    ) -> Result[Position]:
        pos = self.get_position(ai_player_id, symbol)
        if pos is None:
            return Err(f"No position for {symbol}")
        new_qty = pos.quantity * quantity_factor
        new_cost = pos.cost_price / price_factor if price_factor > ZERO else pos.cost_price
        positions = self._positions[ai_player_id]
        positions[symbol] = Position(
            account_id=pos.account_id,
            symbol=symbol,
            quantity=new_qty.quantize(D("0.0001")),
            cost_price=new_cost.quantize(D("0.00000001")),
            market=pos.market,
        )
        return Ok(positions[symbol])

    def get_total_assets_cny(self, ai_player_id: str, market_prices: dict[str, Decimal] | None = None) -> Decimal:
        total = ZERO
        for currency in Currency:
            balance = self.get_balance(ai_player_id, currency)
            if currency == Currency.CNY:
                total += balance
            elif balance > ZERO:
                rate_key = (currency.value, Currency.CNY.value)
                rates = self._exchange_rates.get(rate_key)
                if rates:
                    total += balance * rates["buy_rate"]
        if market_prices:
            for pos in self.get_all_positions(ai_player_id):
                price = market_prices.get(pos.symbol, pos.cost_price)
                position_value_cny = pos.quantity * price
                if pos.market != Market.A_STOCK:
                    src = Currency.USD.value if pos.market == Market.US_STOCK else Currency.USDT.value
                    rate_key = (src, Currency.CNY.value)
                    rates = self._exchange_rates.get(rate_key)
                    if rates:
                        position_value_cny = position_value_cny * rates["buy_rate"]
                total += position_value_cny
        return total

    def get_account_summary(
        self,
        ai_player_id: str,
        market_prices: dict[str, Decimal] | None = None,
    ) -> AccountSummary:
        cash_by_currency = {}
        for currency in Currency:
            balance = self.get_balance(ai_player_id, currency)
            if balance > ZERO:
                cash_by_currency[currency.value] = balance
        total_assets = self.get_total_assets_cny(ai_player_id, market_prices)
        positions = tuple(self.get_all_positions(ai_player_id))
        return AccountSummary(
            ai_player_id=ai_player_id,
            total_assets_cny=total_assets,
            cash_by_currency=cash_by_currency,
            positions=positions,
        )
