from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from src.business.scheduler.scheduler import SimulatorScheduler
from src.core.account.manager import AccountManager
from src.core.constants import ZERO, D
from src.core.enums import SimulationMode

logger = logging.getLogger(__name__)


class BacktestEngine:
    def __init__(self, scheduler: SimulatorScheduler, account_manager: AccountManager) -> None:
        self._scheduler = scheduler
        self._account_mgr = account_manager
        self._speed_multiplier = 100
        self._current_time: datetime | None = None

    async def run(
        self,
        ai_players: list[str],
        start_date: datetime,
        end_date: datetime,
        kline_data: dict[str, list[dict]] | None = None,
        on_cycle_complete: Callable | None = None,
    ) -> dict[str, Any]:
        self._scheduler.set_mode(SimulationMode.BACKTEST)
        self._scheduler.start()
        self._current_time = start_date
        total_cycles = 0
        results: dict[str, Any] = {}

        while self._current_time < end_date and self._scheduler.is_running:
            market_prices = self._get_prices_at_time(kline_data, self._current_time) if kline_data else {}

            if market_prices:
                cycle_results = await self._scheduler.decision_cycle(
                    ai_players, {}, market_prices
                )
                total_cycles += 1
                for r in cycle_results:
                    results.setdefault(r.ai_player_id, {"cycles": 0, "executed": 0})
                    results[r.ai_player_id]["cycles"] += 1
                    results[r.ai_player_id]["executed"] += r.decisions_executed

                if on_cycle_complete:
                    on_cycle_complete(cycle_results)

            self._current_time = self._advance_to_next_session(self._current_time, end_date)

        self._scheduler.stop()
        return {"total_cycles": total_cycles, "results": results}

    def _advance_to_next_session(self, current: datetime, end: datetime) -> datetime:
        next_time = current + timedelta(minutes=5)
        if next_time > end:
            return end
        hour, minute = next_time.hour, next_time.minute
        if hour < 9 or (hour == 9 and minute < 30):
            return next_time.replace(hour=9, minute=30)
        if hour == 11 and minute > 30:
            next_time = next_time.replace(hour=13, minute=0)
            return next_time
        if hour > 15:
            next_day = (next_time + timedelta(days=1)).replace(hour=9, minute=30, second=0, microsecond=0)
            return next_day
        return next_time

    @staticmethod
    def _get_prices_at_time(kline_data: dict, timestamp: datetime) -> dict[str, Decimal]:
        prices: dict[str, Decimal] = {}
        for symbol, bars in kline_data.items():
            latest_price = ZERO
            for bar in bars:
                bar_time = bar.get("timestamp")
                if bar_time and bar_time <= timestamp:
                    latest_price = D(str(bar.get("close", "0")))
            if latest_price > ZERO:
                prices[symbol] = latest_price
        return prices

    @property
    def current_time(self) -> datetime | None:
        return self._current_time

    @property
    def speed_multiplier(self) -> int:
        return self._speed_multiplier
