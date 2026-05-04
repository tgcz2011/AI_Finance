import decimal
from src.core.enums import (
    Currency, Market, Action, SimulationMode, WALStatus,
    OperationType, RiskRuleType, ModuleStatus, MarketStatus,
    PriceLimitStatus, ContestRoundType, AlertLevel,
)
from src.core.constants import (
    D, ZERO, ONE, HUNDRED, INITIAL_CAPITAL_CNY,
    A_STOCK_LOT_SIZE, DECIMAL_PRECISION, CONTEXT_MAX_TOKENS,
)


class TestEnums:
    def test_currency_values(self):
        assert Currency.CNY.value == "CNY"
        assert Currency.USD.value == "USD"
        assert Currency.USDT.value == "USDT"

    def test_market_values(self):
        assert Market.A_STOCK.value == "A_STOCK"
        assert Market.US_STOCK.value == "US_STOCK"
        assert Market.CRYPTO.value == "CRYPTO"

    def test_action_values(self):
        assert Action.BUY.value == "BUY"
        assert Action.SELL.value == "SELL"
        assert Action.HOLD.value == "HOLD"

    def test_simulation_mode(self):
        assert SimulationMode.REALTIME.value == "REALTIME"
        assert SimulationMode.BACKTEST.value == "BACKTEST"

    def test_wal_status(self):
        assert WALStatus.PENDING.value == "PENDING"
        assert WALStatus.COMMITTED.value == "COMMITTED"
        assert WALStatus.ROLLED_BACK.value == "ROLLED_BACK"

    def test_module_status(self):
        assert ModuleStatus.RUNNING.value == "RUNNING"
        assert ModuleStatus.DISABLED.value == "DISABLED"

    def test_risk_rule_type(self):
        assert len(RiskRuleType) == 5

    def test_all_enums_importable(self):
        assert Currency is not None
        assert Market is not None
        assert Action is not None


class TestConstants:
    def test_decimal_precision(self):
        assert decimal.getcontext().prec == 28

    def test_decimal_rounding(self):
        assert decimal.getcontext().rounding == decimal.ROUND_HALF_EVEN

    def test_d_helper(self):
        val = D("123.456")
        assert isinstance(val, decimal.Decimal)
        assert val == decimal.Decimal("123.456")

    def test_zero_one_hundred(self):
        assert ZERO == D("0")
        assert ONE == D("1")
        assert HUNDRED == D("100")

    def test_initial_capital(self):
        assert INITIAL_CAPITAL_CNY == D("1000000")

    def test_a_stock_lot_size(self):
        assert A_STOCK_LOT_SIZE == 100

    def test_decimal_precision_constant(self):
        assert DECIMAL_PRECISION == 8

    def test_no_float_constants(self):
        import src.core.constants as c
        for name in dir(c):
            if name.startswith("_"):
                continue
            val = getattr(c, name)
            if isinstance(val, float):
                raise AssertionError(f"Float constant found: {name} = {val}")
