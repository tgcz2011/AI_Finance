from decimal import Decimal

from src.infrastructure.storage.models import (
    AccountORM,
    AIPlayerORM,
    AuditLogORM,
    Base,
    ContestORM,
    ExchangeRateORM,
    LoanORM,
    PositionORM,
    RiskEventORM,
    SnapshotORM,
    SymbolWhitelistORM,
    TradeORM,
    WALLogORM,
)


class TestModels:
    def test_account_orm_creation(self):
        account = AccountORM(
            id="acc_001",
            ai_player_id="ai_001",
            currency="CNY",
            balance=Decimal("1000000"),
        )
        assert account.id == "acc_001"
        assert account.balance == Decimal("1000000")

    def test_position_orm_creation(self):
        pos = PositionORM(
            account_id="acc_001",
            symbol="600519.SH",
            quantity=Decimal("100"),
            cost_price=Decimal("1800"),
            market="A_STOCK",
        )
        assert pos.symbol == "600519.SH"
        assert pos.quantity == Decimal("100")

    def test_trade_orm_creation(self):
        trade = TradeORM(
            account_id="acc_001",
            symbol="600519.SH",
            action="BUY",
            quantity=Decimal("100"),
            price=Decimal("1800"),
            total_cost=Decimal("180054"),
            currency="CNY",
        )
        assert trade.action == "BUY"
        assert trade.total_cost == Decimal("180054")

    def test_loan_orm_creation(self):
        loan = LoanORM(
            account_id="acc_001",
            principal=Decimal("500000"),
            daily_rate=Decimal("0.0005"),
            is_active=True,
        )
        assert loan.principal == Decimal("500000")
        assert loan.is_active is True

    def test_ai_player_orm_creation(self):
        player = AIPlayerORM(
            id="ai_001",
            name="GPT-4 Trader",
            model_endpoint="https://api.openai.com/v1",
            is_active=True,
        )
        assert player.name == "GPT-4 Trader"
        assert player.is_active is True

    def test_contest_orm_creation(self):
        contest = ContestORM(
            name="Test Contest",
            initial_capital=Decimal("1000000"),
            current_round=1,
            is_active=False,
        )
        assert contest.current_round == 1
        assert contest.is_active is False

    def test_exchange_rate_orm_creation(self):
        rate = ExchangeRateORM(
            from_currency="USD",
            to_currency="CNY",
            mid_rate=Decimal("7.2"),
            buy_rate=Decimal("7.18"),
            sell_rate=Decimal("7.22"),
        )
        assert rate.sell_rate > rate.buy_rate

    def test_wal_log_orm_creation(self):
        wal = WALLogORM(
            operation_type="TRADE_BUY",
            status="PENDING",
            params_json='{"symbol": "600519.SH"}',
            checksum="abc123",
        )
        assert wal.status == "PENDING"

    def test_snapshot_orm_creation(self):
        snap = SnapshotORM(
            version=1,
            data='{"key": "value"}',
            checksum="sha256hash",
        )
        assert snap.version == 1

    def test_symbol_whitelist_orm_creation(self):
        wl = SymbolWhitelistORM(
            symbol="600519.SH",
            market="A_STOCK",
            min_quantity=Decimal("100"),
            quantity_precision=0,
            is_active=True,
        )
        assert wl.is_active is True

    def test_risk_event_orm_creation(self):
        event = RiskEventORM(
            ai_player_id="ai_001",
            rule_type="DRAWDOWN_CIRCUIT_BREAKER",
            details="Drawdown exceeded 30%",
            is_resolved=False,
        )
        assert event.is_resolved is False

    def test_audit_log_orm_creation(self):
        audit = AuditLogORM(
            ai_player_id="ai_001",
            decision_json='{"decisions": []}',
            reasoning="Market is volatile",
            interception_count=0,
        )
        assert audit.interception_count == 0

    def test_all_tables_defined(self):
        table_names = Base.metadata.tables.keys()
        expected = {
            "accounts", "positions", "trades", "loans", "risk_events",
            "audit_logs", "snapshots", "wal_log", "system_logs",
            "ai_players", "contests", "contest_rounds", "contest_players",
            "exchange_rates", "symbol_whitelist",
        }
        assert expected.issubset(table_names), f"Missing tables: {expected - table_names}"
