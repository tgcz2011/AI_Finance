from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.business.loan.manager import LoanManager
from src.core.account.manager import AccountManager
from src.core.constants import AI_DECISION_TIMEOUT_SECONDS, ZERO, D
from src.core.enums import Action, Market, SimulationMode
from src.core.risk.engine import RiskEngine
from src.core.trade_validator.models import TradeOrder
from src.core.trade_validator.validator import TradeValidator
from src.core.types.event_bus import EventBus

logger = logging.getLogger(__name__)


@dataclass
class DecisionCycleResult:
    ai_player_id: str
    decisions_made: int = 0
    decisions_intercepted: int = 0
    decisions_executed: int = 0
    errors: list[str] = field(default_factory=list)


class SimulatorScheduler:
    def __init__(
        self,
        account_manager: AccountManager,
        trade_validator: TradeValidator,
        risk_engine: RiskEngine,
        loan_manager: LoanManager,
        event_bus: EventBus,
    ) -> None:
        self._account_mgr = account_manager
        self._validator = trade_validator
        self._risk = risk_engine
        self._loan = loan_manager
        self._event_bus = event_bus
        self._mode = SimulationMode.REALTIME
        self._running = False
        self._decision_callbacks: dict[str, Any] = {}
        self._market_hours: dict[Market, tuple[str, str]] = {
            Market.A_STOCK: ("09:30", "15:00"),
            Market.US_STOCK: ("09:30", "16:00"),
            Market.CRYPTO: ("00:00", "23:59"),
        }
        self._event_triggers: list[dict] = []

    def set_mode(self, mode: SimulationMode) -> None:
        self._mode = mode

    def register_ai_callback(self, ai_player_id: str, callback: Any) -> None:
        self._decision_callbacks[ai_player_id] = callback

    async def decision_cycle(
        self,
        ai_players: list[str],
        market_data: dict[str, Any],
        market_prices: dict[str, Decimal],
    ) -> list[DecisionCycleResult]:
        results = []
        tasks = [
            self._process_single_ai(ai_id, market_data, market_prices)
            for ai_id in ai_players
        ]
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(completed):
            if isinstance(result, Exception):
                results.append(DecisionCycleResult(
                    ai_player_id=ai_players[i],
                    errors=[str(result)],
                ))
            else:
                results.append(result)
        return results

    async def _process_single_ai(
        self,
        ai_player_id: str,
        market_data: dict[str, Any],
        market_prices: dict[str, Decimal],
    ) -> DecisionCycleResult:
        result = DecisionCycleResult(ai_player_id=ai_player_id)
        summary = self._account_mgr.get_account_summary(ai_player_id, market_prices)

        risk_result = self._risk.check(ai_player_id, summary)
        if risk_result.triggered:
            return result

        callback = self._decision_callbacks.get(ai_player_id)
        if callback is None:
            result.errors.append(f"No callback for {ai_player_id}")
            return result

        try:
            decisions = await asyncio.wait_for(
                callback(ai_player_id, summary, market_data),
                timeout=AI_DECISION_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            return result
        except Exception as e:
            result.errors.append(str(e))
            return result

        result.decisions_made = len(decisions)
        for decision in decisions:
            order = TradeOrder(
                symbol=decision.get("symbol", ""),
                action=Action(decision.get("action", "HOLD")),
                quantity=D(str(decision.get("quantity", "0"))),
                price=market_prices.get(decision.get("symbol", ""), ZERO),
                ai_player_id=ai_player_id,
            )
            validation = self._validator.validate(order)
            if not validation.is_valid:
                result.decisions_intercepted += 1
                continue
            result.decisions_executed += 1
        return result

    def is_market_open(self, market: Market, current_time: datetime | None = None) -> bool:
        if market == Market.CRYPTO:
            return True
        now = current_time or datetime.now()
        time_str = now.strftime("%H:%M")
        open_time, close_time = self._market_hours.get(market, ("00:00", "23:59"))
        return open_time <= time_str <= close_time

    def add_event_trigger(self, symbol: str, price_threshold: Decimal, direction: str = "above") -> None:
        self._event_triggers.append({
            "symbol": symbol,
            "threshold": price_threshold,
            "direction": direction,
        })

    def check_event_triggers(self, market_prices: dict[str, Decimal]) -> list[str]:
        triggered = []
        for trigger in self._event_triggers:
            price = market_prices.get(trigger["symbol"])
            if price is None:
                continue
            above_hit = trigger["direction"] == "above" and price > trigger["threshold"]
            below_hit = trigger["direction"] == "below" and price < trigger["threshold"]
            if above_hit or below_hit:
                triggered.append(trigger["symbol"])
        return triggered

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False
