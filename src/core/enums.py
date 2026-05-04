from __future__ import annotations

from enum import Enum


class Currency(Enum):
    CNY = "CNY"
    USD = "USD"
    USDT = "USDT"
    HKD = "HKD"
    EUR = "EUR"


class Market(Enum):
    A_STOCK = "A_STOCK"
    US_STOCK = "US_STOCK"
    CRYPTO = "CRYPTO"


class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SimulationMode(Enum):
    REALTIME = "REALTIME"
    BACKTEST = "BACKTEST"


class WALStatus(Enum):
    PENDING = "PENDING"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"


class OperationType(Enum):
    TRADE_BUY = "TRADE_BUY"
    TRADE_SELL = "TRADE_SELL"
    CURRENCY_EXCHANGE = "CURRENCY_EXCHANGE"
    LOAN_DISBURSE = "LOAN_DISBURSE"
    LOAN_REPAY = "LOAN_REPAY"
    LOAN_INTEREST = "LOAN_INTEREST"
    DIVIDEND = "DIVIDEND"
    EX_RIGHTS = "EX_RIGHTS"
    SNAPSHOT = "SNAPSHOT"


class RiskRuleType(Enum):
    DRAWDOWN_CIRCUIT_BREAKER = "DRAWDOWN_CIRCUIT_BREAKER"
    CONCENTRATION_LIMIT = "CONCENTRATION_LIMIT"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    ABNORMAL_FREQUENCY = "ABNORMAL_FREQUENCY"
    EXTREME_MARKET = "EXTREME_MARKET"


class ModuleStatus(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


class MarketStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PRE_MARKET = "PRE_MARKET"
    AFTER_HOURS = "AFTER_HOURS"
    HALTED = "HALTED"


class PriceLimitStatus(Enum):
    NORMAL = "NORMAL"
    LIMIT_UP = "LIMIT_UP"
    LIMIT_DOWN = "LIMIT_DOWN"


class ContestRoundType(Enum):
    ELIMINATION = "ELIMINATION"
    POINTS = "POINTS"


class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
