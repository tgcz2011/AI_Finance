from decimal import Decimal

import pytest

from src.core.account.manager import AccountManager
from src.core.constants import D, ZERO, INITIAL_CAPITAL_CNY
from src.core.enums import Currency, Market
from src.core.trade_executor.fee_calculator import FeeCalculator, SlippageCalculator, FeeDetail
from src.core.enums import Action
from src.business.loan.manager import LoanManager


class TestFeeCalculator:
    def test_a_stock_buy_fee(self):
        calc = FeeCalculator()
        fee = calc.calculate_fee(Market.A_STOCK, Action.BUY, D("100"), D("1800"))
        assert fee.commission >= D("5")
        assert fee.stamp_tax == ZERO

    def test_a_stock_sell_includes_stamp_tax(self):
        calc = FeeCalculator()
        fee = calc.calculate_fee(Market.A_STOCK, Action.SELL, D("100"), D("1800"))
        assert fee.stamp_tax > ZERO
        assert fee.total_fee > fee.commission

    def test_a_stock_min_commission(self):
        calc = FeeCalculator()
        fee = calc.calculate_fee(Market.A_STOCK, Action.BUY, D("1"), D("10"))
        assert fee.commission == D("5")

    def test_us_stock_fee(self):
        calc = FeeCalculator()
        fee = calc.calculate_fee(Market.US_STOCK, Action.BUY, D("10"), D("150"))
        assert fee.commission > ZERO
        assert fee.stamp_tax == ZERO

    def test_crypto_fee(self):
        calc = FeeCalculator()
        fee = calc.calculate_fee(Market.CRYPTO, Action.BUY, D("0.1"), D("42000"))
        assert fee.commission > ZERO


class TestSlippageCalculator:
    def test_buy_slippage_increases_price(self):
        calc = SlippageCalculator()
        exec_price = calc.calculate_execution_price(D("100"), Action.BUY)
        assert exec_price > D("100")

    def test_sell_slippage_decreases_price(self):
        calc = SlippageCalculator()
        exec_price = calc.calculate_execution_price(D("100"), Action.SELL)
        assert exec_price < D("100")

    def test_slippage_cost_buy(self):
        calc = SlippageCalculator()
        cost = calc.calculate_slippage_cost(D("100"), Action.BUY, D("100"))
        assert cost > ZERO


class TestLoanManager:
    def _setup(self):
        acct = AccountManager()
        acct.create_account("ai_001", Currency.CNY, INITIAL_CAPITAL_CNY)
        loan_mgr = LoanManager(acct)
        loan_mgr.set_initial_assets("ai_001", INITIAL_CAPITAL_CNY)
        return acct, loan_mgr

    def test_disburse_loan(self):
        acct, loan_mgr = self._setup()
        result = loan_mgr.disburse("ai_001", D("100000"))
        assert result.is_ok
        assert acct.get_balance("ai_001", Currency.CNY) == INITIAL_CAPITAL_CNY + D("100000")

    def test_loan_increases_debt(self):
        acct, loan_mgr = self._setup()
        loan_mgr.disburse("ai_001", D("100000"))
        assert loan_mgr.get_total_debt("ai_001") == D("100000")

    def test_daily_interest_compound(self):
        acct, loan_mgr = self._setup()
        loan_mgr.disburse("ai_001", D("100000"))
        result = loan_mgr.apply_daily_interest("ai_001")
        assert result.is_ok
        assert result.value > ZERO
        debt = loan_mgr.get_total_debt("ai_001")
        assert debt > D("100000")

    def test_collateral_ratio_ok(self):
        acct, loan_mgr = self._setup()
        loan_mgr.disburse("ai_001", D("100000"))
        ratio = loan_mgr.get_collateral_ratio("ai_001", INITIAL_CAPITAL_CNY + D("100000"))
        assert ratio > ZERO

    def test_check_collateral(self):
        acct, loan_mgr = self._setup()
        loan_mgr.disburse("ai_001", D("100000"))
        status = loan_mgr.check_collateral("ai_001", INITIAL_CAPITAL_CNY + D("100000"))
        assert status == "OK"

    def test_repay_loan(self):
        acct, loan_mgr = self._setup()
        loan_mgr.disburse("ai_001", D("100000"))
        loan_mgr.apply_daily_interest("ai_001")
        result = loan_mgr.repay("ai_001", D("100050"))
        assert result.is_ok
        debt = loan_mgr.get_total_debt("ai_001")
        assert debt < D("100000")

    def test_auto_loan_triggered(self):
        acct, loan_mgr = self._setup()
        acct.debit_cash("ai_001", Currency.CNY, INITIAL_CAPITAL_CNY)
        result = loan_mgr.check_auto_loan("ai_001", D("100000"))
        assert result.is_ok
        assert result.value > ZERO

    def test_auto_loan_not_needed(self):
        acct, loan_mgr = self._setup()
        result = loan_mgr.check_auto_loan("ai_001", D("100000"))
        assert result.is_ok
        assert result.value == ZERO

    def test_max_loan_limit(self):
        acct, loan_mgr = self._setup()
        acct.debit_cash("ai_001", Currency.CNY, INITIAL_CAPITAL_CNY)
        loan_mgr.check_auto_loan("ai_001", D("600000"))
        result = loan_mgr.check_auto_loan("ai_001", D("600000"))
        assert result.is_err
