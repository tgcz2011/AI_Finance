
from src.auxiliary.logging_.manager import LogManager
from src.auxiliary.report.generator import ReportGenerator
from src.auxiliary.snapshot.manager import SnapshotManager
from src.core.constants import ZERO, D


class TestSnapshotManager:
    def test_create_snapshot(self, tmp_path):
        mgr = SnapshotManager(snapshot_dir=tmp_path)
        result = mgr.create_snapshot({"accounts": {"ai_001": "1000000"}})
        assert result.is_ok
        assert result.value == 1

    def test_restore_snapshot(self, tmp_path):
        mgr = SnapshotManager(snapshot_dir=tmp_path)
        mgr.create_snapshot({"key": "value"})
        result = mgr.restore(1)
        assert result.is_ok
        assert result.value["key"] == "value"

    def test_restore_nonexistent_fails(self, tmp_path):
        mgr = SnapshotManager(snapshot_dir=tmp_path)
        result = mgr.restore(999)
        assert result.is_err

    def test_list_snapshots(self, tmp_path):
        mgr = SnapshotManager(snapshot_dir=tmp_path)
        mgr.create_snapshot({"a": 1})
        mgr.create_snapshot({"b": 2})
        versions = mgr.list_snapshots()
        assert versions == [1, 2]

    def test_latest_version(self, tmp_path):
        mgr = SnapshotManager(snapshot_dir=tmp_path)
        assert mgr.get_latest_version() == 0
        mgr.create_snapshot({})
        assert mgr.get_latest_version() == 1


class TestLogManager:
    def test_mask_sensitive(self):
        assert LogManager.mask_sensitive("sk-1234567890abcdef") == "sk-1***cdef"
        assert LogManager.mask_sensitive("short") == "***"

    def test_log_decision(self):
        mgr = LogManager()
        mgr.log_decision_request("ai_001", [{"action": "BUY"}])
        logs = mgr.get_recent_logs(1)
        assert len(logs) == 1
        assert logs[0]["category"] == "DECISION_REQUEST"

    def test_log_interception(self):
        mgr = LogManager()
        mgr.log_interception("ai_001", "INVALID", "Not in whitelist")
        logs = mgr.get_recent_logs(1)
        assert logs[0]["category"] == "INTERCEPTION"

    def test_log_trade_execution(self):
        mgr = LogManager()
        mgr.log_trade_execution("acc_001", "AAPL", "BUY", 10, 150)
        logs = mgr.get_recent_logs(1)
        assert "BUY" in logs[0]["message"]


class TestReportGenerator:
    def test_performance_report(self):
        gen = ReportGenerator()
        report = gen.generate_performance_report(
            "ai_001", D("1000000"), D("1200000"),
            daily_returns=[D("0.01")] * 10 + [D("-0.005")] * 5,
            trade_count=100, win_count=60, loan_cost=D("5000"),
        )
        assert report["ai_player_id"] == "ai_001"
        assert D(report["return_rate"]) > ZERO

    def test_max_drawdown(self):
        returns = [D("0.1"), D("-0.2"), D("0.05")]
        dd = ReportGenerator._calculate_max_drawdown(returns)
        assert dd > ZERO

    def test_export_json(self, tmp_path):
        gen = ReportGenerator()
        gen.export_json({"key": "value"}, tmp_path / "report.json")
        assert (tmp_path / "report.json").exists()

    def test_export_csv(self, tmp_path):
        gen = ReportGenerator()
        data = [{"name": "test", "value": 42}]
        gen.export_csv(data, tmp_path / "report.csv")
        assert (tmp_path / "report.csv").exists()

    def test_export_html(self, tmp_path):
        gen = ReportGenerator()
        data = [{"name": "test", "value": 42}]
        gen.export_html("Test Report", data, tmp_path / "report.html")
        assert (tmp_path / "report.html").exists()
