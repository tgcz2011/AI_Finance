from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.core.types.result import Err, Ok, Result
from src.infrastructure.config.models import SystemConfig


def _decimal_representer(dumper: yaml.Dumper, data: Decimal) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))

yaml.add_representer(Decimal, _decimal_representer)


class ConfigManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        if config_dir is None:
            config_dir = Path("config")
        self._config_dir = config_dir
        self._config: SystemConfig | None = None
        self._config_path = config_dir / "system.yaml"

    def load(self, path: Path | None = None) -> Result[SystemConfig]:
        config_path = path or self._config_path
        try:
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
            else:
                raw = {}
            config = SystemConfig.model_validate(raw)
            self._config = config
            return Ok(config)
        except ValidationError as e:
            return Err(f"Config validation error: {e}")
        except Exception as e:
            return Err(f"Config load error: {e}")

    def save(self, config: SystemConfig, path: Path | None = None) -> Result[None]:
        config_path = path or self._config_path
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            raw = config.model_dump(mode="python")
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(raw, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            self._config = config
            return Ok(None)
        except Exception as e:
            return Err(f"Config save error: {e}")

    @property
    def config(self) -> SystemConfig:
        if self._config is None:
            raise RuntimeError("Config not loaded. Call load() first.")
        return self._config

    def update(self, updates: dict) -> Result[SystemConfig]:
        if self._config is None:
            return Err("Config not loaded")
        try:
            current = self._config.model_dump(mode="python")
            self._deep_update(current, updates)
            new_config = SystemConfig.model_validate(current)
            self._config = new_config
            return Ok(new_config)
        except ValidationError as e:
            return Err(f"Config validation error: {e}")

    @staticmethod
    def _deep_update(target: dict, source: dict) -> None:
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                ConfigManager._deep_update(target[key], value)
            else:
                target[key] = value

    def reload(self) -> Result[SystemConfig]:
        return self.load()

    def get_module_config(self) -> dict[str, bool]:
        if self._config is None:
            raise RuntimeError("Config not loaded")
        return self._config.modules.model_dump()
