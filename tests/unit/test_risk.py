from decimal import Decimal

import pytest

from src.core.account.models import AccountSummary, Position
from src.core.constants import D, ZERO
from src.core.enums import Market
from src.core.risk.rules import (
    DrawdownCircuitBreaker, ConcentrationLimit, DailyLossLimit,
    AbnormalFrequencyDetector, ExtremeMarketCircuitBreaker, RiskCheckResult,
)
from src.core.risk.engine import RiskEngine
from src.core.types.event_bus import EventBus


def _make_summary(total_assets: Decimal = D("1000000")) -> AccountSummary:
    return AccountSummary(ai_player_id="ai_001", total_assets_cny=total_assets)


class TestRiskRules:
    def test_drawdown_not_triggered(self):
        rule = DrawdownCircuitBreaker(D("0.3"))
        summary = _make_summary(D("800000"))
        result = rule.evaluate(summary, peak_assets=D("1000000"))
        assert not result.triggered

    def test_drawdown_triggered(self):
        rule = DrawdownCircuitBreaker(D("0.3"))
        summary = _make_summary(D("600000"))
        result = rule.evaluate(summary, peak_assets=D("1000000"))
        assert result.triggered
        assert result.should_pause

    def test_concentration_not_triggered(self):
        rule = ConcentrationLimit(D("0.4"))
        summary = _make_summary()
        result = rule.evaluate(summary, symbol="AAPL", position_value=D("300000"))
        assert not result.triggered

    def test_concentration_triggered(self):
        rule = ConcentrationLimit(D("0.4"))
        summary = _make_summary()
        result = rule.evaluate(summary, symbol="AAPL", position_value=D("500000"))
        assert result.triggered

    def test_daily_loss_not_triggered(self):
        rule = DailyLossLimit(D("0.05"), D("1000000"))
        summary = _make_summary()
        result = rule.evaluate(summary, daily_loss=D("-40000"))
        assert not result.triggered

    def test_daily_loss_triggered(self):
        rule = DailyLossLimit(D("0.05"), D("1000000"))
        summary = _make_summary()
        result = rule.evaluate(summary, daily_loss=D("-60000"))
        assert result.triggered
        assert result.should_pause

    def test_abnormal_frequency_not_triggered(self):
        rule = AbnormalFrequencyDetector(20)
        summary = _make_summary()
        result = rule.evaluate(summary, trades_last_minute=10)
        assert not result.triggered

    def test_abnormal_frequency_triggered(self):
        rule = AbnormalFrequencyDetector(20)
        summary = _make_summary()
        result = rule.evaluate(summary, trades_last_minute=25)
        assert result.triggered

    def test_extreme_market_index_triggered(self):
        rule = ExtremeMarketCircuitBreaker(D("0.05"), D("0.1"))
        summary = _make_summary()
        result = rule.evaluate(summary, market_index_drop=D("0.06"))
        assert result.triggered
        assert result.is_system_wide

    def test_extreme_market_crypto_triggered(self):
        rule = ExtremeMarketCircuitBreaker(D("0.05"), D("0.1"))
        summary = _make_summary()
        result = rule.evaluate(summary, crypto_drop=D("0.15"))
        assert result.triggered
        assert result.is_system_wide


class TestRiskEngine:
    def test_no_rules_passes(self):
        engine = RiskEngine()
        summary = _make_summary()
        result = engine.check("ai_001", summary)
        assert not result.triggered

    def test_drawdown_circuit_breaker_pauses_ai(self):
        bus = EventBus()
        engine = RiskEngine(bus)
        engine.add_rule(DrawdownCircuitBreaker(D("0.3")))
        summary = _make_summary(D("600000"))
        result = engine.check("ai_001", summary, peak_assets=D("1000000"))
        assert result.triggered
        assert "ai_001" in engine.paused_ai_players

    def test_can_resume_after_recovery(self):
        engine = RiskEngine()
        engine.add_rule(DrawdownCircuitBreaker(D("0.3")))
        summary = _make_summary(D("600000"))
        engine.check("ai_001", summary, peak_assets=D("1000000"))
        recovered_summary = _make_summary(D("800000"))
        assert engine.can_resume("ai_001", recovered_summary, peak_assets=D("1000000"))

    def test_resume_ai(self):
        engine = RiskEngine()
        engine.add_rule(DrawdownCircuitBreaker(D("0.3")))
        summary = _make_summary(D("600000"))
        engine.check("ai_001", summary, peak_assets=D("1000000"))
        engine.resume_ai("ai_001")
        assert "ai_001" not in engine.paused_ai_players

    def test_system_wide_pause(self):
        engine = RiskEngine()
        engine.add_rule(ExtremeMarketCircuitBreaker(D("0.05"), D("0.1")))
        summary = _make_summary()
        engine.check("ai_001", summary, market_index_drop=D("0.06"))
        assert engine.is_system_paused

    def test_resume_system(self):
        engine = RiskEngine()
        engine.add_rule(ExtremeMarketCircuitBreaker(D("0.05"), D("0.1")))
        summary = _make_summary()
        engine.check("ai_001", summary, market_index_drop=D("0.06"))
        engine.resume_system()
        assert not engine.is_system_paused
