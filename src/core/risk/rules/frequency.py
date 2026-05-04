from __future__ import annotations

from src.core.account.models import AccountSummary
from src.core.risk.rules.base import RiskCheckResult, RiskRule


class AbnormalFrequencyDetector(RiskRule):
    def __init__(self, max_per_minute: int = 20) -> None:
        self._max_per_minute = max_per_minute

    @property
    def name(self) -> str:
        return "ABNORMAL_FREQUENCY"

    def evaluate(self, summary: AccountSummary, **kwargs) -> RiskCheckResult:
        trades_last_minute = kwargs.get("trades_last_minute", 0)
        if trades_last_minute > self._max_per_minute:
            return RiskCheckResult(
                triggered=True, rule_name=self.name,
                details=f"Frequency {trades_last_minute} > max {self._max_per_minute}/min",
                should_pause=True,
            )
        return RiskCheckResult(triggered=False, rule_name=self.name)
