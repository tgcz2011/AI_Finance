import pytest
from src.core.types.event_bus import EventBus
from src.gui.bridge import GUIBackendBridge
from src.gui.main_window import MainWindow


class TestGUIBackendBridge:
    def test_register_handler(self):
        bus = EventBus()
        bridge = GUIBackendBridge(bus)
        bridge.register_handler("test_action", lambda p: p)
        assert "test_action" in bridge._request_handlers

    @pytest.mark.asyncio
    async def test_request(self):
        bus = EventBus()
        bridge = GUIBackendBridge(bus)
        bridge.register_handler("add", lambda p: p.get("a", 0) + p.get("b", 0))
        result = await bridge.request("add", {"a": 1, "b": 2})
        assert result == 3

    @pytest.mark.asyncio
    async def test_request_unknown_action(self):
        bus = EventBus()
        bridge = GUIBackendBridge(bus)
        with pytest.raises(ValueError):
            await bridge.request("unknown")

    def test_subscribe_realtime(self):
        bus = EventBus()
        bridge = GUIBackendBridge(bus)
        received = []
        bridge.subscribe_realtime("channel", lambda p: received.append(p))
        assert "channel" in bridge._realtime_subscribers

    def test_backend_ready(self):
        bus = EventBus()
        bridge = GUIBackendBridge(bus)
        assert not bridge.is_backend_ready
        bridge.set_backend_ready(True)
        assert bridge.is_backend_ready


class TestMainWindow:
    def test_nav_items(self):
        bus = EventBus()
        bridge = GUIBackendBridge(bus)
        window = MainWindow(bridge)
        assert len(window.nav_items) == 8

    def test_set_view(self):
        bus = EventBus()
        bridge = GUIBackendBridge(bus)
        window = MainWindow(bridge)
        window.set_view("排行榜")
        assert window.current_view == "排行榜"
