import decimal
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.constants import INITIAL_CAPITAL_CNY, D


@pytest.fixture
def decimal_context():
    ctx = decimal.getcontext()
    old_prec = ctx.prec
    ctx.prec = 28
    yield ctx
    ctx.prec = old_prec


@pytest.fixture
def mock_db_engine():
    engine = MagicMock()
    engine.begin = AsyncMock()
    return engine


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    return session


@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    bus.publish = MagicMock()
    bus.publish_async = AsyncMock()
    bus.subscribe = MagicMock()
    return bus


@pytest.fixture
def mock_data_fetcher():
    fetcher = AsyncMock()
    fetcher.fetch_market_data = AsyncMock(return_value=[])
    fetcher.get_whitelist = AsyncMock(return_value=set())
    fetcher.get_exchange_rate = AsyncMock(return_value=D("7.2"))
    return fetcher


@pytest.fixture
def mock_ai_service():
    service = AsyncMock()
    service.chat_completions_create = AsyncMock()
    return service


@pytest.fixture
def sample_account_id() -> str:
    return "ai_player_001"


@pytest.fixture
def sample_initial_capital() -> Decimal:
    return INITIAL_CAPITAL_CNY


@pytest.fixture
def sample_symbol_a_stock() -> str:
    return "600519.SH"


@pytest.fixture
def sample_symbol_us_stock() -> str:
    return "AAPL"


@pytest.fixture
def sample_symbol_crypto() -> str:
    return "BTC/USDT"


@pytest.fixture
def sample_timestamp() -> datetime:
    return datetime(2026, 1, 1, 9, 30, 0)


@pytest.fixture
def sample_market_price() -> dict[str, Decimal]:
    return {
        "600519.SH": D("1800.00"),
        "AAPL": D("150.00"),
        "BTC/USDT": D("42000.00"),
    }
