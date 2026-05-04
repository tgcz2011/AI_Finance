

from src.core.account.manager import AccountManager
from src.core.constants import INITIAL_CAPITAL_CNY, D
from src.core.enums import Action, Currency, Market, MarketStatus, PriceLimitStatus
from src.core.trade_validator.models import TradeOrder
from src.core.trade_validator.validator import TradeValidator


class TestTradeValidator:
    def _setup(self):
        acct = AccountManager()
        acct.create_account("ai_001", Currency.CNY, INITIAL_CAPITAL_CNY)
        acct.create_account("ai_001", Currency.USD, D("100000"))
        acct.create_account("ai_001", Currency.USDT, D("100000"))
        validator = TradeValidator(acct)
        validator.set_whitelist({
            "600519.SH": {"market": Market.A_STOCK.value, "min_quantity": D("100"), "quantity_precision": 0},
            "AAPL": {"market": Market.US_STOCK.value, "min_quantity": D("1"), "quantity_precision": 0},
            "BTC/USDT": {"market": Market.CRYPTO.value, "min_quantity": D("0.0001"), "quantity_precision": 4},
        })
        validator.set_market_status({
            "600519.SH": MarketStatus.OPEN,
            "AAPL": MarketStatus.OPEN,
            "BTC/USDT": MarketStatus.OPEN,
        })
        return acct, validator

    def test_hold_always_valid(self):
        _, validator = self._setup()
        order = TradeOrder(symbol="600519.SH", action=Action.HOLD, quantity=D("0"))
        result = validator.validate(order)
        assert result.is_valid

    def test_symbol_not_in_whitelist(self):
        _, validator = self._setup()
        order = TradeOrder(symbol="INVALID", action=Action.BUY, quantity=D("100"), price=D("10"))
        result = validator.validate(order)
        assert not result.is_valid
        assert "whitelist" in result.reason

    def test_a_stock_quantity_lot_size(self):
        _, validator = self._setup()
        order = TradeOrder(
            symbol="600519.SH", action=Action.BUY,
            quantity=D("150"), price=D("1800"), ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert result.is_valid
        assert result.adjusted_quantity == D("100")

    def test_us_stock_quantity_rounds_down(self):
        _, validator = self._setup()
        order = TradeOrder(
            symbol="AAPL", action=Action.BUY,
            quantity=D("10.5"), price=D("150"), ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert result.is_valid
        assert result.adjusted_quantity == D("10")

    def test_crypto_quantity_precision(self):
        _, validator = self._setup()
        order = TradeOrder(
            symbol="BTC/USDT", action=Action.BUY,
            quantity=D("0.123456"), price=D("42000"), ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert result.is_valid
        assert result.adjusted_quantity == D("0.1235")

    def test_halted_market_rejects(self):
        _, validator = self._setup()
        validator.set_market_status({"600519.SH": MarketStatus.HALTED})
        order = TradeOrder(
            symbol="600519.SH", action=Action.BUY,
            quantity=D("100"), price=D("1800"), ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert not result.is_valid
        assert "halted" in result.reason

    def test_limit_up_rejects_buy(self):
        _, validator = self._setup()
        validator.set_price_limits({"600519.SH": PriceLimitStatus.LIMIT_UP})
        order = TradeOrder(
            symbol="600519.SH", action=Action.BUY,
            quantity=D("100"), price=D("1800"), ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert not result.is_valid
        assert "limit up" in result.reason

    def test_limit_down_rejects_sell(self):
        acct, validator = self._setup()
        acct.add_position("ai_001", "600519.SH", D("100"), D("1800"), Market.A_STOCK)
        validator.set_price_limits({"600519.SH": PriceLimitStatus.LIMIT_DOWN})
        order = TradeOrder(
            symbol="600519.SH", action=Action.SELL,
            quantity=D("100"), price=D("1620"), ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert not result.is_valid
        assert "limit down" in result.reason

    def test_insufficient_funding_rejects(self):
        _acct, validator = self._setup()
        order = TradeOrder(
            symbol="600519.SH", action=Action.BUY,
            quantity=D("10000"), price=D("1800"), ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert not result.is_valid

    def test_insufficient_holding_rejects(self):
        _acct, validator = self._setup()
        order = TradeOrder(
            symbol="600519.SH", action=Action.SELL,
            quantity=D("100"), price=D("1800"), ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert not result.is_valid
