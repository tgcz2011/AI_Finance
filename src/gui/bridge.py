from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable

from src.core.types.event_bus import EventBus, Event


class GUIBackendBridge:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._backend_ready = False
        self._request_handlers: dict[str, Callable] = {}
        self._realtime_subscribers: dict[str, list[Callable]] = {}

    def register_handler(self, action: str, handler: Callable) -> None:
        self._request_handlers[action] = handler

    async def request(self, action: str, payload: dict | None = None) -> Any:
        handler = self._request_handlers.get(action)
        if handler is None:
            raise ValueError(f"No handler for action: {action}")
        if inspect.iscoroutinefunction(handler):
            return await handler(payload or {})
        return handler(payload or {})

    def subscribe_realtime(self, channel: str, callback: Callable) -> None:
        self._realtime_subscribers.setdefault(channel, []).append(callback)
        self._event_bus.subscribe(channel, lambda e: self._dispatch(channel, e))

    def _dispatch(self, channel: str, event: Event) -> None:
        for callback in self._realtime_subscribers.get(channel, []):
            try:
                callback(event.payload)
            except Exception:
                pass

    @property
    def is_backend_ready(self) -> bool:
        return self._backend_ready

    def set_backend_ready(self, ready: bool) -> None:
        self._backend_ready = ready
