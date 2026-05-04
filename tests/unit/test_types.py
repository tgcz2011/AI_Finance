import pytest
from src.core.types.result import Ok, Err, Result
from src.core.types.event_bus import EventBus, Event, EventPriority


class TestOk:
    def test_is_ok(self):
        r = Ok(42)
        assert r.is_ok is True
        assert r.is_err is False

    def test_value_or_none(self):
        r = Ok("hello")
        assert r.value_or_none == "hello"

    def test_error_or_none(self):
        r = Ok(42)
        assert r.error_or_none is None

    def test_unwrap(self):
        r = Ok(42)
        assert r.unwrap() == 42

    def test_unwrap_or(self):
        r = Ok(42)
        assert r.unwrap_or(0) == 42

    def test_map(self):
        r = Ok(10)
        r2 = r.map(lambda x: x * 2)
        assert isinstance(r2, Ok)
        assert r2.value == 20

    def test_frozen(self):
        r = Ok(42)
        with pytest.raises(AttributeError):
            r.value = 99


class TestErr:
    def test_is_err(self):
        r = Err("error msg")
        assert r.is_err is True
        assert r.is_ok is False

    def test_value_or_none(self):
        r = Err("error")
        assert r.value_or_none is None

    def test_error_or_none(self):
        r = Err("error msg")
        assert r.error_or_none == "error msg"

    def test_unwrap_raises(self):
        r = Err("error")
        with pytest.raises(ValueError):
            r.unwrap()

    def test_unwrap_or(self):
        r = Err("error")
        assert r.unwrap_or(0) == 0

    def test_map(self):
        r = Err("error")
        r2 = r.map(lambda x: x * 2)
        assert isinstance(r2, Err)
        assert r2.error == "error"

    def test_frozen(self):
        r = Err("error")
        with pytest.raises(AttributeError):
            r.error = "new"


class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe("test_event", lambda e: received.append(e.payload))
        bus.publish(Event(event_type="test_event", payload="data"))
        assert received == ["data"]

    def test_multiple_subscribers(self):
        bus = EventBus()
        results = []
        bus.subscribe("evt", lambda e: results.append("a"))
        bus.subscribe("evt", lambda e: results.append("b"))
        bus.publish(Event(event_type="evt"))
        assert results == ["a", "b"]

    def test_unsubscribe(self):
        bus = EventBus()
        received = []
        handler = lambda e: received.append(1)
        bus.subscribe("evt", handler)
        bus.unsubscribe("evt", handler)
        bus.publish(Event(event_type="evt"))
        assert received == []

    def test_priority_ordering(self):
        bus = EventBus()
        results = []
        bus.subscribe("evt", lambda e: results.append("low"), EventPriority.LOW)
        bus.subscribe("evt", lambda e: results.append("high"), EventPriority.HIGH)
        bus.subscribe("evt", lambda e: results.append("normal"), EventPriority.NORMAL)
        bus.publish(Event(event_type="evt"))
        assert results == ["high", "normal", "low"]

    def test_no_subscriber_no_error(self):
        bus = EventBus()
        bus.publish(Event(event_type="unknown"))

    def test_clear(self):
        bus = EventBus()
        bus.subscribe("evt", lambda e: None)
        bus.clear()
        assert bus._subscribers == {}

    @pytest.mark.asyncio
    async def test_async_publish(self):
        bus = EventBus()
        received = []
        async def handler(e):
            received.append(e.payload)
        bus.subscribe_async("evt", handler)
        await bus.publish_async(Event(event_type="evt", payload="async_data"))
        assert received == ["async_data"]
