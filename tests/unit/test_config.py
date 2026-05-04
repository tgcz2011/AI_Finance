from decimal import Decimal
from pathlib import Path

import pytest

from src.infrastructure.config.models import SystemConfig, FeeConfig, LoanConfig
from src.infrastructure.config.manager import ConfigManager


class TestConfigModels:
    def test_default_config_valid(self):
        config = SystemConfig()
        assert config.initial_capital_cny == Decimal("1000000")
        assert config.simulation_mode == "REALTIME"

    def test_fee_config_defaults(self):
        fee = FeeConfig()
        assert fee.a_stock_commission_bps == Decimal("0.0003")
        assert fee.a_stock_commission_min == Decimal("5")

    def test_loan_config_defaults(self):
        loan = LoanConfig()
        assert loan.daily_interest_rate == Decimal("0.0005")
        assert loan.collateral_liquidation_ratio < loan.collateral_warning_ratio

    def test_invalid_simulation_mode(self):
        with pytest.raises(Exception):
            SystemConfig(simulation_mode="INVALID")

    def test_exchange_fee_max_lt_min_invalid(self):
        with pytest.raises(Exception):
            FeeConfig(exchange_fee_min_bps=Decimal("0.005"), exchange_fee_max_bps=Decimal("0.001"))

    def test_liquidation_gte_warning_invalid(self):
        with pytest.raises(Exception):
            LoanConfig(
                collateral_warning_ratio=Decimal("1.1"),
                collateral_liquidation_ratio=Decimal("1.2"),
            )

    def test_modules_config_defaults(self):
        config = SystemConfig()
        assert config.modules.account is True
        assert config.modules.version_control is False


class TestConfigManager:
    def test_load_default_config(self, tmp_path):
        config_path = tmp_path / "system.yaml"
        config_path.write_text("initial_capital_cny: '500000'\n")
        mgr = ConfigManager(config_dir=tmp_path)
        result = mgr.load(path=config_path)
        assert result.is_ok
        assert result.value.initial_capital_cny == Decimal("500000")

    def test_load_nonexistent_uses_defaults(self, tmp_path):
        mgr = ConfigManager(config_dir=tmp_path)
        result = mgr.load()
        assert result.is_ok
        assert result.value.initial_capital_cny == Decimal("1000000")

    def test_save_and_reload(self, tmp_path):
        mgr = ConfigManager(config_dir=tmp_path)
        config = SystemConfig(initial_capital_cny=Decimal("2000000"))
        save_result = mgr.save(config)
        assert save_result.is_ok
        mgr2 = ConfigManager(config_dir=tmp_path)
        load_result = mgr2.load()
        assert load_result.is_ok
        assert load_result.value.initial_capital_cny == Decimal("2000000")

    def test_update_config(self, tmp_path):
        mgr = ConfigManager(config_dir=tmp_path)
        mgr.load()
        result = mgr.update({"initial_capital_cny": "3000000"})
        assert result.is_ok
        assert result.value.initial_capital_cny == Decimal("3000000")

    def test_update_invalid_value_returns_err(self, tmp_path):
        mgr = ConfigManager(config_dir=tmp_path)
        mgr.load()
        result = mgr.update({"simulation_mode": "INVALID"})
        assert result.is_err

    def test_config_not_loaded_raises(self, tmp_path):
        mgr = ConfigManager(config_dir=tmp_path)
        with pytest.raises(RuntimeError):
            _ = mgr.config

    def test_get_module_config(self, tmp_path):
        mgr = ConfigManager(config_dir=tmp_path)
        mgr.load()
        module_config = mgr.get_module_config()
        assert module_config["account"] is True
        assert module_config["version_control"] is False

    def test_reload(self, tmp_path):
        config_path = tmp_path / "system.yaml"
        config_path.write_text("initial_capital_cny: '999999'\n")
        mgr = ConfigManager(config_dir=tmp_path)
        mgr.load(path=config_path)
        result = mgr.reload()
        assert result.is_ok
        assert result.value.initial_capital_cny == Decimal("999999")
