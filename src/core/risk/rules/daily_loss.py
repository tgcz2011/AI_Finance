from __future__ import annotations

from decimal import Decimal

from src.core.account.models import AccountSummary
from src.core.constants import ZERO, D
from src.core.risk.rules.base import RiskCheckResult, RiskRule

_DAILY_LOSS_DEFAULT_RATIO = D("0.05")


class DailyLossLimit(RiskRule):
    def __init__(self, ratio: Decimal = _DAILY_LOSS_DEFAULT_RATIO, initial_assets: Decimal = ZERO) -> None:
        self._ratio = ratio
        self._initial_assets = initial_assets

    @property
    def name(self) -> str:
        return "DAILY_LOSS_LIMIT"

    def evaluate(self, summary: AccountSummary, **kwargs) -> RiskCheckResult:
        daily_loss = kwargs.get("daily_loss", ZERO)
        if self._initial_assets <= ZERO:
            return RiskCheckResult(triggered=False, rule_name=self.name)
        loss_ratio = abs(daily_loss) / self._initial_assets
        if loss_ratio > self._ratio:
            return RiskCheckResult(
                triggered=True, rule_name=self.name,
                details=f"Daily loss {loss_ratio:.4%} > limit {self._ratio:.4%}",
                should_pause=True,
            )
        return RiskCheckResult(triggered=False, rule_name=self.name)
