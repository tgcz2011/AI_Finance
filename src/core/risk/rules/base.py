from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.core.account.models import AccountSummary


@dataclass(frozen=True)
class RiskCheckResult:
    triggered: bool
    rule_name: str
    details: str = ""
    should_pause: bool = False
    is_system_wide: bool = False


class RiskRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def evaluate(self, summary: AccountSummary, **kwargs) -> RiskCheckResult: ...
