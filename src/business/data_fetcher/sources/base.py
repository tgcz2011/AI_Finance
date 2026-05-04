from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.core.constants import ZERO


@dataclass(frozen=True)
class MarketQuote:
    symbol: str
    price: Decimal
    bid: Decimal = ZERO
    ask: Decimal = ZERO
    change_24h: Decimal = ZERO
    volume: Decimal = ZERO
    is_halted: bool = False
    timestamp: datetime | None = None


class MarketDataSource(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def is_free(self) -> bool: ...

    @property
    @abstractmethod
    def requires_api_key(self) -> bool: ...

    @abstractmethod
    async def fetch_quotes(self, symbols: list[str]) -> list[MarketQuote]: ...

    @abstractmethod
    async def fetch_whitelist(self) -> dict[str, dict]: ...

    async def health_check(self) -> bool:
        try:
            await self.fetch_quotes([])
            return True
        except Exception:
            return False
