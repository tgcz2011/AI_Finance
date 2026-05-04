from __future__ import annotations

import logging
import sys
import typing

logger = logging.getLogger(__name__)


class MainWindow:
    NAV_ITEMS: typing.ClassVar[list[str]] = [
        "主控制", "竞赛控制", "排行榜", "资产曲线",
        "交易记录", "AI绩效", "模块管理", "配置编辑",
    ]

    def __init__(self, bridge) -> None:
        self._bridge = bridge
        self._current_view = "主控制"
        self._views: dict[str, object] = {}
        logger.info("MainWindow initialized")

    def set_view(self, view_name: str) -> None:
        if view_name in self.NAV_ITEMS:
            self._current_view = view_name
            logger.info(f"Switched to view: {view_name}")

    @property
    def current_view(self) -> str:
        return self._current_view

    @property
    def nav_items(self) -> list[str]:
        return list(self.NAV_ITEMS)


def run_gui():
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        from src.core.types.event_bus import EventBus
        from src.gui.bridge import GUIBackendBridge
        bus = EventBus()
        bridge = GUIBackendBridge(bus)
        MainWindow(bridge)
        logger.info("GUI application started")
        sys.exit(app.exec())
    except ImportError:
        logger.error("PyQt6 not installed. Please install with: pip install PyQt6")
        sys.exit(1)
