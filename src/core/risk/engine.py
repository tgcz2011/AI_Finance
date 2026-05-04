from __future__ import annotations

from decimal import Decimal
from typing import Callable

from src.core.account.models import AccountSummary
from src.core.risk.rules import RiskRule, RiskCheckResult
from src.core.types.event_bus import EventBus, Event


class RiskEngine:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._rules: list[RiskRule] = []
        self._event_bus = event_bus
        self._paused_ai: set[str] = set()
        self._system_wide_pause = False

    def add_rule(self, rule: RiskRule) -> None:
        self._rules.append(rule)

    def check(self, ai_player_id: str, summary: AccountSummary, **kwargs) -> RiskCheckResult:
        if self._system_wide_pause:
            return RiskCheckResult(
                triggered=True, rule_name="SYSTEM_WIDE",
                details="System-wide pause active", should_pause=True, is_system_wide=True,
            )
        if ai_player_id in self._paused_ai:
            return RiskCheckResult(
                triggered=True, rule_name="AI_PAUSED",
                details=f"AI {ai_player_id} is paused", should_pause=True,
            )
        for rule in self._rules:
            result = rule.evaluate(summary, **kwargs)
            if result.triggered:
                if result.should_pause:
                    if result.is_system_wide:
                        self._system_wide_pause = True
                    else:
                        self._paused_ai.add(ai_player_id)
                if self._event_bus:
                    self._event_bus.publish(Event(event_type="risk_triggered", payload=result))
                return result
        return RiskCheckResult(triggered=False, rule_name="")

    def can_resume(self, ai_player_id: str, summary: AccountSummary, **kwargs) -> bool:
        for rule in self._rules:
            result = rule.evaluate(summary, **kwargs)
            if result.triggered and result.should_pause:
                return False
        return True

    def resume_ai(self, ai_player_id: str) -> None:
        self._paused_ai.discard(ai_player_id)

    def resume_system(self) -> None:
        self._system_wide_pause = False

    @property
    def paused_ai_players(self) -> frozenset[str]:
        return frozenset(self._paused_ai)

    @property
    def is_system_paused(self) -> bool:
        return self._system_wide_pause
