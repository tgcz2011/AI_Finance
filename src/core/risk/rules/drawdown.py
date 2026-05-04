from __future__ import annotations

from decimal import Decimal

from src.core.account.models import AccountSummary
from src.core.constants import D, ZERO
from src.core.risk.rules.base import RiskRule, RiskCheckResult


class DrawdownCircuitBreaker(RiskRule):
    def __init__(self, threshold: Decimal = D("0.3")) -> None:
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "DRAWDOWN_CIRCUIT_BREAKER"

    def evaluate(self, summary: AccountSummary, **kwargs) -> RiskCheckResult:
        peak_assets = kwargs.get("peak_assets", summary.total_assets_cny)
        if peak_assets <= ZERO:
            return RiskCheckResult(triggered=False, rule_name=self.name)
        drawdown = (peak_assets - summary.total_assets_cny) / peak_assets
        if drawdown >= self._threshold:
            return RiskCheckResult(
                triggered=True, rule_name=self.name,
                details=f"Drawdown {drawdown:.4%} >= threshold {self._threshold:.4%}",
                should_pause=True,
            )
        return RiskCheckResult(triggered=False, rule_name=self.name)
