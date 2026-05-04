
from src.auxiliary.snapshot.manager import SnapshotManager
from src.business.contest.manager import ContestManager
from src.core.account.manager import AccountManager
from src.core.account.models import AccountSummary
from src.core.constants import INITIAL_CAPITAL_CNY, D
from src.core.enums import Action, Currency, Market, MarketStatus
from src.core.risk.engine import RiskEngine
from src.core.risk.rules import DrawdownCircuitBreaker, ExtremeMarketCircuitBreaker
from src.core.trade_validator.models import TradeOrder
from src.core.trade_validator.validator import TradeValidator
from src.core.types.event_bus import EventBus


class TestTradeFlow:
    def test_buy_a_stock_full_flow(self):
        acct = AccountManager()
        acct.create_account("ai_001", Currency.CNY, INITIAL_CAPITAL_CNY)
        validator = TradeValidator(acct)
        validator.set_whitelist({
            "600519.SH": {"market": Market.A_STOCK.value, "min_quantity": D("100"), "quantity_precision": 0},
        })
        validator.set_market_status({"600519.SH": MarketStatus.OPEN})
        order = TradeOrder(
            symbol="600519.SH", action=Action.BUY,
            quantity=D("100"), price=D("1800"),
            ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert result.is_valid
        debit_result = acct.debit_cash("ai_001", Currency.CNY, D("180000"))
        assert debit_result.is_ok
        pos_result = acct.add_position("ai_001", "600519.SH", D("100"), D("1800"), Market.A_STOCK)
        assert pos_result.is_ok
        assert acct.get_balance("ai_001", Currency.CNY) == D("820000")

    def test_sell_a_stock_full_flow(self):
        acct = AccountManager()
        acct.create_account("ai_001", Currency.CNY, INITIAL_CAPITAL_CNY)
        acct.add_position("ai_001", "600519.SH", D("100"), D("1800"), Market.A_STOCK)
        validator = TradeValidator(acct)
        validator.set_whitelist({
            "600519.SH": {"market": Market.A_STOCK.value, "min_quantity": D("100"), "quantity_precision": 0},
        })
        validator.set_market_status({"600519.SH": MarketStatus.OPEN})
        order = TradeOrder(
            symbol="600519.SH", action=Action.SELL,
            quantity=D("100"), price=D("1850"),
            ai_player_id="ai_001",
        )
        result = validator.validate(order)
        assert result.is_valid
        reduce_result = acct.reduce_position("ai_001", "600519.SH", D("100"))
        assert reduce_result.is_ok
        acct.credit_cash("ai_001", Currency.CNY, D("185000"))
        assert acct.get_balance("ai_001", Currency.CNY) > INITIAL_CAPITAL_CNY


class TestContestFlow:
    def test_contest_full_lifecycle(self):
        acct = AccountManager()
        contest = ContestManager(acct)
        contest.create_contest(["ai_001", "ai_002"], D("1000000"))
        contest.start_contest()
        assert contest.is_active
        acct.credit_cash("ai_001", Currency.CNY, D("50000"))
        leaderboard = contest.get_leaderboard()
        assert leaderboard[0].ai_player_id == "ai_001"
        contest.stop_contest()
        assert not contest.is_active


class TestRiskFlow:
    def test_drawdown_circuit_breaker_flow(self):
        bus = EventBus()
        engine = RiskEngine(bus)
        engine.add_rule(DrawdownCircuitBreaker(D("0.3")))
        summary = AccountSummary(ai_player_id="ai_001", total_assets_cny=D("600000"))
        result = engine.check("ai_001", summary, peak_assets=D("1000000"))
        assert result.triggered
        assert "ai_001" in engine.paused_ai_players
        recovered = AccountSummary(ai_player_id="ai_001", total_assets_cny=D("800000"))
        assert engine.can_resume("ai_001", recovered, peak_assets=D("1000000"))
        engine.resume_ai("ai_001")
        assert "ai_001" not in engine.paused_ai_players

    def test_system_wide_pause_flow(self):
        bus = EventBus()
        engine = RiskEngine(bus)
        engine.add_rule(ExtremeMarketCircuitBreaker(D("0.05"), D("0.1")))
        summary = AccountSummary(ai_player_id="ai_001", total_assets_cny=D("1000000"))
        result = engine.check("ai_001", summary, market_index_drop=D("0.06"))
        assert result.triggered
        assert engine.is_system_paused
        engine.resume_system()
        assert not engine.is_system_paused


class TestRecoveryFlow:
    def test_snapshot_create_and_restore(self, tmp_path):
        mgr = SnapshotManager(snapshot_dir=tmp_path)
        state = {"accounts": {"ai_001": "1000000"}, "positions": {}}
        v = mgr.create_snapshot(state)
        assert v.is_ok
        restored = mgr.restore(v.value)
        assert restored.is_ok
        assert restored.value["accounts"]["ai_001"] == "1000000"
