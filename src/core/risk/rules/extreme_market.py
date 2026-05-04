from __future__ import annotations

from decimal import Decimal

from src.core.account.models import AccountSummary
from src.core.constants import ZERO, D
from src.core.risk.rules.base import RiskCheckResult, RiskRule

_EXTREME_INDEX_DROP = D("0.05")
_EXTREME_CRYPTO_DROP = D("0.1")


class ExtremeMarketCircuitBreaker(RiskRule):
    def __init__(self, index_drop: Decimal = _EXTREME_INDEX_DROP, crypto_drop: Decimal = _EXTREME_CRYPTO_DROP) -> None:
        self._index_drop = index_drop
        self._crypto_drop = crypto_drop

    @property
    def name(self) -> str:
        return "EXTREME_MARKET"

    def evaluate(self, summary: AccountSummary, **kwargs) -> RiskCheckResult:
        market_index_drop = kwargs.get("market_index_drop", ZERO)
        crypto_drop = kwargs.get("crypto_drop", ZERO)
        if market_index_drop >= self._index_drop:
            return RiskCheckResult(
                triggered=True, rule_name=self.name,
                details=f"Market index drop {market_index_drop:.4%} >= threshold",
                should_pause=True, is_system_wide=True,
            )
        if crypto_drop >= self._crypto_drop:
            return RiskCheckResult(
                triggered=True, rule_name=self.name,
                details=f"Crypto drop {crypto_drop:.4%} >= threshold",
                should_pause=True, is_system_wide=True,
            )
        return RiskCheckResult(triggered=False, rule_name=self.name)
