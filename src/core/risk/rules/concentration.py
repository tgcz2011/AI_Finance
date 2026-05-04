from __future__ import annotations

from decimal import Decimal

from src.core.account.models import AccountSummary
from src.core.constants import ZERO, D
from src.core.risk.rules.base import RiskCheckResult, RiskRule

_CONCENTRATION_DEFAULT_LIMIT = D("0.4")


class ConcentrationLimit(RiskRule):
    def __init__(self, limit: Decimal = _CONCENTRATION_DEFAULT_LIMIT) -> None:
        self._limit = limit

    @property
    def name(self) -> str:
        return "CONCENTRATION_LIMIT"

    def evaluate(self, summary: AccountSummary, **kwargs) -> RiskCheckResult:
        symbol = kwargs.get("symbol", "")
        position_value = kwargs.get("position_value", ZERO)
        if summary.total_assets_cny <= ZERO:
            return RiskCheckResult(triggered=False, rule_name=self.name)
        concentration = position_value / summary.total_assets_cny
        if concentration > self._limit:
            return RiskCheckResult(
                triggered=True, rule_name=self.name,
                details=f"Concentration {concentration:.4%} > limit {self._limit:.4%} for {symbol}",
            )
        return RiskCheckResult(triggered=False, rule_name=self.name)
