from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


DECIMAL_TYPE = Numeric(20, 8, asdecimal=True)


class AccountORM(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ai_player_id: Mapped[str] = mapped_column(String(64), ForeignKey("ai_players.id"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    balance: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("ai_player_id", "currency", name="uq_account_currency"),
        CheckConstraint("balance >= 0", name="ck_account_balance_nonneg"),
    )


class PositionORM(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False, default=Decimal("0"))
    cost_price: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False, default=Decimal("0"))
    market: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("account_id", "symbol", name="uq_position_symbol"),
        CheckConstraint("quantity >= 0", name="ck_position_qty_nonneg"),
        CheckConstraint("cost_price >= 0", name="ck_position_cost_nonneg"),
        Index("ix_position_account", "account_id"),
    )


class TradeORM(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    fee: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False, default=Decimal("0"))
    slippage_cost: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False, default=Decimal("0"))
    exchange_cost: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False, default=Decimal("0"))
    total_cost: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_trade_qty_pos"),
        CheckConstraint("price > 0", name="ck_trade_price_pos"),
        Index("ix_trade_account_time", "account_id", "executed_at"),
    )


class LoanORM(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.id"), nullable=False)
    principal: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    interest_accrued: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False, default=Decimal("0"))
    daily_rate: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    disbursed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    last_interest_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        CheckConstraint("principal > 0", name="ck_loan_principal_pos"),
        CheckConstraint("daily_rate > 0", name="ck_loan_rate_pos"),
        Index("ix_loan_account_active", "account_id", "is_active"),
    )


class RiskEventORM(Base):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ai_player_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(40), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_risk_player_time", "ai_player_id", "triggered_at"),
    )


class AuditLogORM(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ai_player_id: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_json: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    interception_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    context_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("ix_audit_player_time", "ai_player_id", "created_at"),
    )


class SnapshotORM(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("ix_snapshot_version", "version"),
    )


class WALLogORM(Base):
    __tablename__ = "wal_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    params_json: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_wal_status", "status"),
    )


class SystemLogORM(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("ix_syslog_time", "created_at"),
    )


class AIPlayerORM(Base):
    __tablename__ = "ai_players"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_endpoint: Mapped[str] = mapped_column(String(256), nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_params_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)


class ContestORM(Base):
    __tablename__ = "contests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    initial_capital: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    round_type: Mapped[str] = mapped_column(String(20), nullable=False, default="POINTS")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        CheckConstraint("initial_capital > 0", name="ck_contest_capital_pos"),
    )


class ContestRoundORM(Base):
    __tablename__ = "contest_rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contest_id: Mapped[int] = mapped_column(Integer, ForeignKey("contests.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    daily_rate_override: Mapped[Decimal | None] = mapped_column(DECIMAL_TYPE, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("contest_id", "round_number", name="uq_contest_round"),
    )


class ContestPlayerORM(Base):
    __tablename__ = "contest_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contest_id: Mapped[int] = mapped_column(Integer, ForeignKey("contests.id"), nullable=False)
    ai_player_id: Mapped[str] = mapped_column(String(64), ForeignKey("ai_players.id"), nullable=False)
    is_eliminated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_points: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False, default=Decimal("0"))

    __table_args__ = (
        UniqueConstraint("contest_id", "ai_player_id", name="uq_contest_player"),
    )


class ExchangeRateORM(Base):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    mid_rate: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    buy_rate: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    sell_rate: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("from_currency", "to_currency", name="uq_exchange_pair"),
    )


class SymbolWhitelistORM(Base):
    __tablename__ = "symbol_whitelist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    market: Mapped[str] = mapped_column(String(20), nullable=False)
    min_quantity: Mapped[Decimal] = mapped_column(DECIMAL_TYPE, nullable=False)
    quantity_precision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
