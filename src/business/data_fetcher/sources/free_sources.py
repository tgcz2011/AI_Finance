from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from src.business.data_fetcher.sources.base import MarketDataSource, MarketQuote
from src.core.constants import D, ZERO
from src.core.enums import Market


class AKShareSource(MarketDataSource):
    @property
    def name(self) -> str:
        return "AKShare"

    @property
    def is_free(self) -> bool:
        return True

    @property
    def requires_api_key(self) -> bool:
        return False

    async def fetch_quotes(self, symbols: list[str]) -> list[MarketQuote]:
        try:
            import akshare as ak
            quotes = []
            for symbol in symbols:
                try:
                    df = ak.stock_zh_a_spot_em()
                    row = df[df["代码"] == symbol.replace(".SH", "").replace(".SZ", "")]
                    if not row.empty:
                        price = D(str(row.iloc[0]["最新价"]))
                        quotes.append(MarketQuote(symbol=symbol, price=price))
                except Exception:
                    pass
            return quotes
        except ImportError:
            return []

    async def fetch_whitelist(self) -> dict[str, dict]:
        return {}


class YFinanceSource(MarketDataSource):
    @property
    def name(self) -> str:
        return "YFinance"

    @property
    def is_free(self) -> bool:
        return True

    @property
    def requires_api_key(self) -> bool:
        return False

    async def fetch_quotes(self, symbols: list[str]) -> list[MarketQuote]:
        try:
            import yfinance as yf
            quotes = []
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.fast_info
                    price = D(str(info.last_price))
                    quotes.append(MarketQuote(symbol=symbol, price=price))
                except Exception:
                    pass
            return quotes
        except ImportError:
            return []

    async def fetch_whitelist(self) -> dict[str, dict]:
        return {}


class CoinGeckoSource(MarketDataSource):
    @property
    def name(self) -> str:
        return "CoinGecko"

    @property
    def is_free(self) -> bool:
        return True

    @property
    def requires_api_key(self) -> bool:
        return False

    async def fetch_quotes(self, symbols: list[str]) -> list[MarketQuote]:
        return []

    async def fetch_whitelist(self) -> dict[str, dict]:
        return {}
