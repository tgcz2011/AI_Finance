from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.core.constants import D, ZERO, SNAPSHOT_WRITE_TIMEOUT_SECONDS
from src.core.types.result import Ok, Err, Result

logger = logging.getLogger(__name__)


class SnapshotManager:
    def __init__(self, snapshot_dir: Path = Path("data/snapshots")) -> None:
        self._snapshot_dir = snapshot_dir
        self._version = 0
        self._snapshots: dict[int, dict] = {}

    def create_snapshot(self, system_state: dict[str, Any]) -> Result[int]:
        try:
            self._version += 1
            version = self._version
            data_json = json.dumps(system_state, default=str, sort_keys=True)
            checksum = hashlib.sha256(data_json.encode()).hexdigest()
            self._snapshots[version] = {
                "version": version,
                "data": data_json,
                "checksum": checksum,
                "created_at": datetime.now().isoformat(),
            }
            self._snapshot_dir.mkdir(parents=True, exist_ok=True)
            snapshot_path = self._snapshot_dir / f"snapshot_v{version:06d}.json"
            snapshot_path.write_text(data_json, encoding="utf-8")
            return Ok(version)
        except Exception as e:
            return Err(f"Snapshot creation failed: {e}")

    def restore(self, version: int) -> Result[dict[str, Any]]:
        snapshot = self._snapshots.get(version)
        if snapshot is None:
            return Err(f"Snapshot version {version} not found")
        try:
            data = json.loads(snapshot["data"])
            expected_checksum = snapshot["checksum"]
            actual_checksum = hashlib.sha256(snapshot["data"].encode()).hexdigest()
            if actual_checksum != expected_checksum:
                return Err(f"Snapshot checksum mismatch for version {version}")
            return Ok(data)
        except Exception as e:
            return Err(f"Snapshot restore failed: {e}")

    def list_snapshots(self) -> list[int]:
        return sorted(self._snapshots.keys())

    def get_latest_version(self) -> int:
        return self._version
