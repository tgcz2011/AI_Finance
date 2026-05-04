from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging() -> None:
    Path("data").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/app.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("AI Finance Simulator starting...")

    from src.core.types.event_bus import EventBus
    from src.core.wal.recovery import SystemRecovery
    from src.infrastructure.config.manager import ConfigManager
    from src.infrastructure.module_manager.registry import ModuleRegistry, register_all_modules

    config_mgr = ConfigManager()
    config_result = config_mgr.load()
    if config_result.is_err:
        logger.error(f"Config load failed: {config_result.error}")
        sys.exit(1)

    registry = ModuleRegistry()
    register_all_modules(registry)

    EventBus()
    recovery = SystemRecovery()
    recovery.setup_signal_handlers()

    try:
        from src.gui.main_window import run_gui
        run_gui()
    except ImportError:
        logger.error("PyQt6 not available, cannot start GUI")
        logger.info("Install PyQt6: pip install PyQt6 qasync")
        sys.exit(1)


if __name__ == "__main__":
    main()
