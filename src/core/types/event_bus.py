from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass(frozen=True)
class Event:
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Any = None
    priority: EventPriority = EventPriority.NORMAL


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[tuple[Callable, EventPriority | None]]] = {}
        self._async_subscribers: dict[str, list[tuple[Callable, EventPriority | None]]] = {}

    def subscribe(self, event_type: str, handler: Callable, priority: EventPriority | None = None) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append((handler, priority))

    def subscribe_async(self, event_type: str, handler: Callable, priority: EventPriority | None = None) -> None:
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append((handler, priority))

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                (h, p) for h, p in self._subscribers[event_type] if h != handler
            ]

    def publish(self, event: Event) -> None:
        handlers = self._subscribers.get(event.event_type, [])
        sorted_handlers = sorted(handlers, key=lambda x: x[1].value if x[1] else 0, reverse=True)
        for handler, _ in sorted_handlers:
            handler(event)

    async def publish_async(self, event: Event) -> None:
        sync_handlers = self._subscribers.get(event.event_type, [])
        async_handlers = self._async_subscribers.get(event.event_type, [])
        all_handlers = sorted(
            sync_handlers + async_handlers,
            key=lambda x: x[1].value if x[1] else 0,
            reverse=True,
        )
        for handler, _ in all_handlers:
            if inspect.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)

    def clear(self) -> None:
        self._subscribers.clear()
        self._async_subscribers.clear()
