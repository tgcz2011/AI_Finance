from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class FeeConfig(BaseModel):
    a_stock_commission_bps: Decimal = Field(default=Decimal("0.0003"), ge=0)
    a_stock_commission_min: Decimal = Field(default=Decimal("5"), ge=0)
    a_stock_stamp_tax_bps: Decimal = Field(default=Decimal("0.001"), ge=0)
    us_stock_commission_bps: Decimal = Field(default=Decimal("0.005"), ge=0)
    crypto_taker_fee_bps: Decimal = Field(default=Decimal("0.001"), ge=0)
    crypto_maker_fee_bps: Decimal = Field(default=Decimal("0.001"), ge=0)
    exchange_fee_min_bps: Decimal = Field(default=Decimal("0.001"), ge=0)
    exchange_fee_max_bps: Decimal = Field(default=Decimal("0.004"), ge=0)
    slippage_bps: Decimal = Field(default=Decimal("0.0005"), ge=0)

    @field_validator("exchange_fee_max_bps")
    @classmethod
    def max_gte_min(cls, v, info):
        if "exchange_fee_min_bps" in info.data and v < info.data["exchange_fee_min_bps"]:
            raise ValueError("exchange_fee_max_bps must be >= exchange_fee_min_bps")
        return v


class LoanConfig(BaseModel):
    daily_interest_rate: Decimal = Field(default=Decimal("0.0005"), gt=0)
    max_loan_ratio: Decimal = Field(default=Decimal("0.5"), gt=0, le=1)
    collateral_warning_ratio: Decimal = Field(default=Decimal("1.2"), gt=1)
    collateral_liquidation_ratio: Decimal = Field(default=Decimal("1.1"), gt=1)

    @field_validator("collateral_liquidation_ratio")
    @classmethod
    def liquidation_lt_warning(cls, v, info):
        if "collateral_warning_ratio" in info.data and v >= info.data["collateral_warning_ratio"]:
            raise ValueError("liquidation_ratio must be < warning_ratio")
        return v


class RiskConfig(BaseModel):
    drawdown_circuit_breaker_threshold: Decimal = Field(default=Decimal("0.3"), gt=0, lt=1)
    concentration_limit: Decimal = Field(default=Decimal("0.4"), gt=0, le=1)
    daily_loss_limit_ratio: Decimal = Field(default=Decimal("0.05"), gt=0, lt=1)
    abnormal_frequency_per_minute: int = Field(default=20, gt=0)
    extreme_market_index_drop: Decimal = Field(default=Decimal("0.05"), gt=0)
    extreme_market_crypto_drop: Decimal = Field(default=Decimal("0.1"), gt=0)


class DataFetcherConfig(BaseModel):
    cache_ttl_realtime_seconds: int = Field(default=60, gt=0)
    rate_limit_initial_delay: Decimal = Field(default=Decimal("1"), gt=0)
    rate_limit_max_delay: Decimal = Field(default=Decimal("60"), gt=0)
    rate_limit_backoff_factor: int = Field(default=2, gt=1)
    rate_limit_max_retries: int = Field(default=10, gt=0)
    cross_source_deviation_threshold: Decimal = Field(default=Decimal("0.02"), gt=0)
    fetch_timeout_seconds: int = Field(default=10, gt=0)
    free_source_priority: bool = Field(default=True)


class ContextCompressConfig(BaseModel):
    max_tokens: int = Field(default=4096, gt=0)
    priority_market_state: int = Field(default=4, gt=0)
    priority_recent_trades: int = Field(default=3, gt=0)
    priority_historical_summary: int = Field(default=2, gt=0)
    priority_auxiliary: int = Field(default=1, gt=0)


class AIConfig(BaseModel):
    decision_timeout_seconds: int = Field(default=30, gt=0)
    local_model_priority: bool = Field(default=True)
    context_compress: ContextCompressConfig = Field(default_factory=ContextCompressConfig)


class SnapshotConfig(BaseModel):
    interval_seconds: int = Field(default=3600, gt=0)
    write_timeout_seconds: int = Field(default=5, gt=0)


class GitConfig(BaseModel):
    enabled: bool = Field(default=False)
    auto_commit_on_day_end: bool = Field(default=True)
    auto_commit_on_round_end: bool = Field(default=True)
    auto_commit_on_contest_end: bool = Field(default=True)
    auto_push: bool = Field(default=False)
    github_token_encrypted: str | None = Field(default=None)


class ModulesConfig(BaseModel):
    account: bool = Field(default=True)
    trade_validator: bool = Field(default=True)
    trade_executor: bool = Field(default=True)
    risk: bool = Field(default=True)
    data_fetcher: bool = Field(default=True)
    ai_adapter: bool = Field(default=True)
    loan: bool = Field(default=True)
    scheduler: bool = Field(default=True)
    contest: bool = Field(default=True)
    snapshot: bool = Field(default=True)
    report: bool = Field(default=True)
    logging: bool = Field(default=True)
    version_control: bool = Field(default=False)


class SystemConfig(BaseModel):
    initial_capital_cny: Decimal = Field(default=Decimal("1000000"), gt=0)
    simulation_mode: str = Field(default="REALTIME", pattern="^(REALTIME|BACKTEST)$")
    decimal_precision: int = Field(default=8, gt=0)
    spread_bps: Decimal = Field(default=Decimal("0.004"), ge=0)
    fee: FeeConfig = Field(default_factory=FeeConfig)
    loan: LoanConfig = Field(default_factory=LoanConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    data_fetcher: DataFetcherConfig = Field(default_factory=DataFetcherConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    snapshot: SnapshotConfig = Field(default_factory=SnapshotConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    modules: ModulesConfig = Field(default_factory=ModulesConfig)
