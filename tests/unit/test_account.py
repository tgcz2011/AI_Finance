from decimal import Decimal

import pytest

from src.core.account.manager import AccountManager
from src.core.account.models import Account, Position, AccountSummary
from src.core.constants import D, ZERO, INITIAL_CAPITAL_CNY
from src.core.enums import Currency, Market
from src.core.types.result import Ok, Err


class TestAccountManager:
    def _setup_manager(self) -> AccountManager:
        mgr = AccountManager()
        mgr.create_account("ai_001", Currency.CNY, INITIAL_CAPITAL_CNY)
        mgr.create_account("ai_001", Currency.USD, D("0"))
        mgr.set_exchange_rate(
            Currency.USD, Currency.CNY,
            mid_rate=D("7.2"), buy_rate=D("7.18"), sell_rate=D("7.22"),
        )
        mgr.set_exchange_rate(
            Currency.CNY, Currency.USD,
            mid_rate=D("0.13889"), buy_rate=D("0.13850"), sell_rate=D("0.13928"),
        )
        mgr.set_exchange_rate(
            Currency.USDT, Currency.CNY,
            mid_rate=D("7.1"), buy_rate=D("7.08"), sell_rate=D("7.12"),
        )
        return mgr

    def test_create_account(self):
        mgr = AccountManager()
        result = mgr.create_account("ai_001", Currency.CNY, D("1000000"))
        assert result.is_ok
        assert result.value.balance == D("1000000")

    def test_create_duplicate_account_fails(self):
        mgr = AccountManager()
        mgr.create_account("ai_001", Currency.CNY)
        result = mgr.create_account("ai_001", Currency.CNY)
        assert result.is_err

    def test_get_balance(self):
        mgr = self._setup_manager()
        assert mgr.get_balance("ai_001", Currency.CNY) == INITIAL_CAPITAL_CNY

    def test_debit_cash(self):
        mgr = self._setup_manager()
        result = mgr.debit_cash("ai_001", Currency.CNY, D("100000"))
        assert result.is_ok
        assert result.value.balance == D("900000")

    def test_debit_cash_insufficient(self):
        mgr = self._setup_manager()
        result = mgr.debit_cash("ai_001", Currency.CNY, D("2000000"))
        assert result.is_err

    def test_debit_cash_negative_amount(self):
        mgr = self._setup_manager()
        result = mgr.debit_cash("ai_001", Currency.CNY, D("-100"))
        assert result.is_err

    def test_credit_cash(self):
        mgr = self._setup_manager()
        result = mgr.credit_cash("ai_001", Currency.CNY, D("50000"))
        assert result.is_ok
        assert result.value.balance == D("1050000")

    def test_credit_cash_negative_amount(self):
        mgr = self._setup_manager()
        result = mgr.credit_cash("ai_001", Currency.CNY, D("-100"))
        assert result.is_err

    def test_exchange_currency(self):
        mgr = self._setup_manager()
        result = mgr.exchange_currency("ai_001", Currency.CNY, Currency.USD, D("72000"))
        assert result.is_ok
        usd_received = result.value
        assert usd_received > ZERO
        assert mgr.get_balance("ai_001", Currency.USD) > ZERO
        assert mgr.get_balance("ai_001", Currency.CNY) < INITIAL_CAPITAL_CNY

    def test_exchange_same_currency(self):
        mgr = self._setup_manager()
        result = mgr.exchange_currency("ai_001", Currency.CNY, Currency.CNY, D("1000"))
        assert result.is_ok
        assert result.value == D("1000")

    def test_exchange_insufficient_balance(self):
        mgr = self._setup_manager()
        result = mgr.exchange_currency("ai_001", Currency.USD, Currency.CNY, D("100"))
        assert result.is_err

    def test_add_position(self):
        mgr = self._setup_manager()
        result = mgr.add_position("ai_001", "600519.SH", D("100"), D("1800"), Market.A_STOCK)
        assert result.is_ok
        assert result.value.quantity == D("100")
        assert result.value.cost_price == D("1800")

    def test_add_position_accumulates(self):
        mgr = self._setup_manager()
        mgr.add_position("ai_001", "600519.SH", D("100"), D("1800"), Market.A_STOCK)
        result = mgr.add_position("ai_001", "600519.SH", D("100"), D("1900"), Market.A_STOCK)
        assert result.is_ok
        assert result.value.quantity == D("200")
        assert result.value.cost_price == D("1850")

    def test_reduce_position(self):
        mgr = self._setup_manager()
        mgr.add_position("ai_001", "600519.SH", D("200"), D("1800"), Market.A_STOCK)
        result = mgr.reduce_position("ai_001", "600519.SH", D("100"))
        assert result.is_ok
        cost_price, total_cost = result.value
        assert cost_price == D("1800")
        assert total_cost == D("180000")
        pos = mgr.get_position("ai_001", "600519.SH")
        assert pos.quantity == D("100")

    def test_reduce_position_insufficient(self):
        mgr = self._setup_manager()
        mgr.add_position("ai_001", "600519.SH", D("50"), D("1800"), Market.A_STOCK)
        result = mgr.reduce_position("ai_001", "600519.SH", D("100"))
        assert result.is_err

    def test_reduce_position_all_removes(self):
        mgr = self._setup_manager()
        mgr.add_position("ai_001", "600519.SH", D("100"), D("1800"), Market.A_STOCK)
        mgr.reduce_position("ai_001", "600519.SH", D("100"))
        assert mgr.get_position("ai_001", "600519.SH") is None

    def test_apply_dividend(self):
        mgr = self._setup_manager()
        mgr.add_position("ai_001", "600519.SH", D("100"), D("1800"), Market.A_STOCK)
        result = mgr.apply_dividend("ai_001", "600519.SH", D("10"))
        assert result.is_ok
        assert result.value == D("1000")
        assert mgr.get_balance("ai_001", Currency.CNY) == INITIAL_CAPITAL_CNY + D("1000")

    def test_apply_ex_rights(self):
        mgr = self._setup_manager()
        mgr.add_position("ai_001", "600519.SH", D("100"), D("1800"), Market.A_STOCK)
        result = mgr.apply_ex_rights("ai_001", "600519.SH", D("1.1"), D("1.1"))
        assert result.is_ok
        assert result.value.quantity == D("110.0000")

    def test_get_total_assets_cny(self):
        mgr = self._setup_manager()
        total = mgr.get_total_assets_cny("ai_001")
        assert total == INITIAL_CAPITAL_CNY

    def test_account_isolation(self):
        mgr = AccountManager()
        mgr.create_account("ai_001", Currency.CNY, D("1000000"))
        mgr.create_account("ai_002", Currency.CNY, D("1000000"))
        mgr.debit_cash("ai_001", Currency.CNY, D("500000"))
        assert mgr.get_balance("ai_001", Currency.CNY) == D("500000")
        assert mgr.get_balance("ai_002", Currency.CNY) == D("1000000")

    def test_no_float_in_balances(self):
        mgr = self._setup_manager()
        mgr.debit_cash("ai_001", Currency.CNY, D("0.00000001"))
        balance = mgr.get_balance("ai_001", Currency.CNY)
        assert isinstance(balance, Decimal)

    def test_get_account_summary(self):
        mgr = self._setup_manager()
        summary = mgr.get_account_summary("ai_001")
        assert summary.ai_player_id == "ai_001"
        assert summary.total_assets_cny == INITIAL_CAPITAL_CNY
        assert "CNY" in summary.cash_by_currency
