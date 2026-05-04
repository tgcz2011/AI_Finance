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
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import (
            QApplication,
            QHBoxLayout,
            QLabel,
            QMainWindow,
            QPushButton,
            QStackedWidget,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        logger.error("PyQt6 not installed. Please install with: pip install PyQt6")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("AI Finance Simulator")
    app.setApplicationVersion("0.1.0")

    from src.core.types.event_bus import EventBus
    from src.gui.bridge import GUIBackendBridge

    bus = EventBus()
    GUIBackendBridge(bus)

    window = QMainWindow()
    window.setWindowTitle("AI Finance Simulator v0.1.0")
    window.setMinimumSize(1200, 800)

    central = QWidget()
    h_layout = QHBoxLayout(central)
    h_layout.setContentsMargins(10, 10, 10, 10)

    nav_panel = QWidget()
    nav_layout = QVBoxLayout(nav_panel)
    nav_layout.setSpacing(3)
    title = QLabel("AI Finance Simulator")
    title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    nav_layout.addWidget(title)

    stack = QStackedWidget()
    for i, item in enumerate(MainWindow.NAV_ITEMS):
        btn = QPushButton(item)
        idx = i

        def _switch(_checked=False, index=idx):
            stack.setCurrentIndex(index)

        btn.clicked.connect(_switch)
        nav_layout.addWidget(btn)

        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.addWidget(QLabel(f"{item} - 功能开发中..."))
        page_layout.addStretch()
        stack.addWidget(page)

    nav_layout.addStretch()
    h_layout.addWidget(nav_panel, 1)
    h_layout.addWidget(stack, 5)

    window.setCentralWidget(central)
    window.show()

    logger.info("GUI application started")
    sys.exit(app.exec())
