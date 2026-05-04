import pytest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from src.core.account.manager import AccountManager
from src.core.constants import D, ZERO, INITIAL_CAPITAL_CNY
from src.core.enums import Currency, ContestRoundType
from src.business.contest.manager import ContestManager, LeaderboardEntry


class TestContestManager:
    def _setup(self):
        acct = AccountManager()
        mgr = ContestManager(acct)
        return acct, mgr

    def test_create_contest(self):
        acct, mgr = self._setup()
        result = mgr.create_contest(["ai_001", "ai_002"], INITIAL_CAPITAL_CNY)
        assert result.is_ok
        assert len(mgr.participants) == 2

    def test_start_stop_contest(self):
        acct, mgr = self._setup()
        mgr.create_contest(["ai_001"])
        start = mgr.start_contest()
        assert start.is_ok
        assert mgr.is_active
        mgr.stop_contest()
        assert not mgr.is_active

    def test_leaderboard_ranking(self):
        acct, mgr = self._setup()
        mgr.create_contest(["ai_001", "ai_002"], D("1000000"))
        acct.credit_cash("ai_001", Currency.CNY, D("100000"))
        leaderboard = mgr.get_leaderboard()
        assert len(leaderboard) == 2
        assert leaderboard[0].ai_player_id == "ai_001"
        assert leaderboard[0].rank == 1

    def test_advance_round_points(self):
        acct, mgr = self._setup()
        mgr.create_contest(["ai_001", "ai_002"], D("1000000"), round_type=ContestRoundType.POINTS)
        mgr.start_contest()
        result = mgr.advance_round()
        assert result.is_ok
        assert mgr.current_round == 2
        assert len(mgr.points) > 0

    def test_advance_round_elimination(self):
        acct, mgr = self._setup()
        mgr.create_contest(["ai_001", "ai_002", "ai_003"], D("1000000"), round_type=ContestRoundType.ELIMINATION)
        mgr.start_contest()
        result = mgr.advance_round(elimination_ratio=D("0.33"))
        assert result.is_ok
        assert len(mgr.eliminated) > 0

    def test_contest_not_active_cannot_advance(self):
        acct, mgr = self._setup()
        result = mgr.advance_round()
        assert result.is_err

    def test_duplicate_create_fails(self):
        acct, mgr = self._setup()
        mgr.create_contest(["ai_001"])
        result = mgr.create_contest(["ai_002"])
        assert result.is_err
