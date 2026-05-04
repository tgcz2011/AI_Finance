from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.constants import (
    CONTEXT_MAX_TOKENS,
    CONTEXT_PRIORITY_AUXILIARY,
    CONTEXT_PRIORITY_HISTORICAL_SUMMARY,
    CONTEXT_PRIORITY_MARKET_STATE,
    CONTEXT_PRIORITY_RECENT_TRADES,
)


@dataclass(frozen=True)
class ContextBlock:
    content: str
    priority: int
    token_count: int
    category: str


class ContextCompressor:
    def __init__(self, max_tokens: int = CONTEXT_MAX_TOKENS) -> None:
        self._max_tokens = max_tokens

    def compress(self, context: dict[str, Any]) -> dict[str, Any]:
        system_prompt = context.get("system_prompt", "")
        trading_rules = context.get("trading_rules", "")
        header = f"{system_prompt}\n\n{trading_rules}"

        blocks: list[ContextBlock] = []
        market_state = context.get("market_state", {})
        if market_state:
            blocks.append(ContextBlock(
                content=self._serialize(market_state),
                priority=CONTEXT_PRIORITY_MARKET_STATE,
                token_count=self._estimate_tokens(market_state),
                category="MARKET_STATE",
            ))

        recent_trades = context.get("recent_trades", [])
        if recent_trades:
            blocks.append(ContextBlock(
                content=self._serialize(recent_trades),
                priority=CONTEXT_PRIORITY_RECENT_TRADES,
                token_count=self._estimate_tokens(recent_trades),
                category="RECENT_TRADES",
            ))

        historical = context.get("historical_summary", {})
        if historical:
            blocks.append(ContextBlock(
                content=self._serialize(historical),
                priority=CONTEXT_PRIORITY_HISTORICAL_SUMMARY,
                token_count=self._estimate_tokens(historical),
                category="HISTORICAL_SUMMARY",
            ))

        auxiliary = context.get("auxiliary", {})
        if auxiliary:
            blocks.append(ContextBlock(
                content=self._serialize(auxiliary),
                priority=CONTEXT_PRIORITY_AUXILIARY,
                token_count=self._estimate_tokens(auxiliary),
                category="AUXILIARY",
            ))

        header_tokens = self._estimate_tokens_str(header)
        remaining = self._max_tokens - header_tokens

        sorted_blocks = sorted(blocks, key=lambda b: b.priority, reverse=True)
        included = []
        for block in sorted_blocks:
            if remaining <= 0:
                break
            if block.token_count <= remaining:
                included.append(block)
                remaining -= block.token_count
            elif block.category == "RECENT_TRADES":
                compressed = self._compress_trades(recent_trades, remaining)
                included.append(ContextBlock(
                    content=compressed,
                    priority=block.priority,
                    token_count=self._estimate_tokens_str(compressed),
                    category="RECENT_TRADES_COMPRESSED",
                ))
                remaining = 0
            elif block.category == "HISTORICAL_SUMMARY":
                included.append(block)
                remaining -= block.token_count

        compressed_content = header
        for block in included:
            compressed_content += f"\n\n## {block.category}\n{block.content}"

        return {
            "compressed_context": compressed_content,
            "total_tokens": self._estimate_tokens_str(compressed_content),
            "blocks_included": [b.category for b in included],
        }

    @staticmethod
    def _estimate_tokens(data: Any) -> int:
        return len(str(data)) // 4

    @staticmethod
    def _estimate_tokens_str(text: str) -> int:
        return len(text) // 4

    @staticmethod
    def _serialize(data: Any) -> str:
        import json
        return json.dumps(data, default=str, ensure_ascii=False)

    @staticmethod
    def _compress_trades(trades: list, max_tokens: int) -> str:
        if not trades:
            return ""
        total = len(trades)
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        return f"Summary of {total} trades: {wins} wins, total PnL: {total_pnl:.2f}"
