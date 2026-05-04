from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from src.core.account.manager import AccountManager
from src.core.constants import INITIAL_CAPITAL_CNY, ZERO, D
from src.core.enums import ContestRoundType, Currency
from src.core.types.result import Err, Ok, Result

logger = logging.getLogger(__name__)


@dataclass
class LeaderboardEntry:
    ai_player_id: str
    rank: int = 0
    total_assets_cny: Decimal = ZERO
    return_rate: Decimal = ZERO
    max_drawdown: Decimal = ZERO


@dataclass
class ContestRound:
    round_number: int
    round_type: ContestRoundType = ContestRoundType.POINTS
    daily_rate_override: Decimal | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class ContestManager:
    def __init__(self, account_manager: AccountManager) -> None:
        self._account_mgr = account_manager
        self._participants: list[str] = []
        self._initial_capital = INITIAL_CAPITAL_CNY
        self._is_active = False
        self._current_round = 1
        self._duration_days = 30
        self._started_at: datetime | None = None
        self._rounds: list[ContestRound] = []
        self._eliminated: set[str] = set()
        self._points: dict[str, Decimal] = {}
        self._peak_assets: dict[str, Decimal] = {}
        self._round_type = ContestRoundType.POINTS

    def create_contest(
        self,
        ai_players: list[str],
        initial_capital: Decimal = INITIAL_CAPITAL_CNY,
        duration_days: int = 30,
        round_type: ContestRoundType = ContestRoundType.POINTS,
    ) -> Result[None]:
        if self._is_active or self._participants:
            return Err("Contest already exists")
        self._participants = list(ai_players)
        self._initial_capital = initial_capital
        self._duration_days = duration_days
        self._round_type = round_type
        for ai_id in ai_players:
            existing = self._account_mgr.get_account(ai_id, Currency.CNY)
            if existing is None:
                self._account_mgr.create_account(ai_id, Currency.CNY, initial_capital)
            self._points[ai_id] = ZERO
            self._peak_assets[ai_id] = initial_capital
        self._rounds.append(ContestRound(
            round_number=1,
            round_type=round_type,
            started_at=datetime.now(),
        ))
        return Ok(None)

    def start_contest(self) -> Result[None]:
        if not self._participants:
            return Err("No participants")
        self._is_active = True
        self._started_at = datetime.now()
        return Ok(None)

    def stop_contest(self) -> Result[None]:
        self._is_active = False
        if self._rounds:
            self._rounds[-1].ended_at = datetime.now()
        return Ok(None)

    def update_rankings(self, market_prices: dict[str, Decimal] | None = None) -> list[LeaderboardEntry]:
        entries = []
        for ai_id in self._participants:
            if ai_id in self._eliminated:
                continue
            total_assets = self._account_mgr.get_total_assets_cny(ai_id, market_prices)
            if self._initial_capital > ZERO:
                return_rate = (total_assets - self._initial_capital) / self._initial_capital
            else:
                return_rate = ZERO
            if total_assets > self._peak_assets.get(ai_id, ZERO):
                self._peak_assets[ai_id] = total_assets
            entries.append(LeaderboardEntry(
                ai_player_id=ai_id,
                total_assets_cny=total_assets,
                return_rate=return_rate.quantize(D("0.0001")),
            ))
        entries.sort(key=lambda e: e.total_assets_cny, reverse=True)
        for i, entry in enumerate(entries):
            entry.rank = i + 1
            peak = self._peak_assets.get(entry.ai_player_id, entry.total_assets_cny)
            if peak > ZERO:
                entry.max_drawdown = ((peak - entry.total_assets_cny) / peak).quantize(D("0.0001"))
        return entries

    def get_leaderboard(self, market_prices: dict[str, Decimal] | None = None) -> list[LeaderboardEntry]:
        return self.update_rankings(market_prices)

    def advance_round(self, elimination_ratio: Decimal = ZERO) -> Result[None]:
        if not self._is_active:
            return Err("No active contest")
        if self._rounds:
            self._rounds[-1].ended_at = datetime.now()
        self._current_round += 1
        rankings = self.update_rankings()
        if elimination_ratio > ZERO and self._round_type == ContestRoundType.ELIMINATION:
            eliminate_count = max(1, int(len(rankings) * float(elimination_ratio)))
            for entry in rankings[-eliminate_count:]:
                self._eliminated.add(entry.ai_player_id)
        if self._round_type == ContestRoundType.POINTS:
            for i, entry in enumerate(rankings):
                points = D(str(len(rankings) - i))
                self._points[entry.ai_player_id] = self._points.get(entry.ai_player_id, ZERO) + points
        self._rounds.append(ContestRound(
            round_number=self._current_round,
            round_type=self._round_type,
            started_at=datetime.now(),
        ))
        return Ok(None)

    def is_contest_expired(self) -> bool:
        if self._started_at is None:
            return False
        return datetime.now() >= self._started_at + timedelta(days=self._duration_days)

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def participants(self) -> list[str]:
        return [p for p in self._participants if p not in self._eliminated]

    @property
    def current_round(self) -> int:
        return self._current_round

    @property
    def points(self) -> dict[str, Decimal]:
        return dict(self._points)

    @property
    def eliminated(self) -> frozenset[str]:
        return frozenset(self._eliminated)
