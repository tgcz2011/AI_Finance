
from src.business.ai_adapter.context_compressor import ContextCompressor


class TestContextCompressor:
    def test_compress_preserves_header(self):
        comp = ContextCompressor(max_tokens=10000)
        context = {
            "system_prompt": "You are a trading AI.",
            "trading_rules": "Buy low sell high.",
            "market_state": {"600519.SH": {"price": 1800}},
            "recent_trades": [{"symbol": "AAPL", "pnl": 100}],
        }
        result = comp.compress(context)
        assert "You are a trading AI." in result["compressed_context"]
        assert "Buy low sell high." in result["compressed_context"]

    def test_compress_includes_market_state(self):
        comp = ContextCompressor(max_tokens=10000)
        context = {
            "system_prompt": "Test",
            "trading_rules": "",
            "market_state": {"AAPL": 150},
        }
        result = comp.compress(context)
        assert "MARKET_STATE" in result["compressed_context"]

    def test_compress_truncates_low_priority(self):
        comp = ContextCompressor(max_tokens=100)
        context = {
            "system_prompt": "Short",
            "trading_rules": "",
            "market_state": {"AAPL": 150},
            "auxiliary": {"x" * 10000: 1},
        }
        result = comp.compress(context)
        assert result["total_tokens"] <= 120

    def test_compress_empty_context(self):
        comp = ContextCompressor()
        result = comp.compress({})
        assert "compressed_context" in result

    def test_compress_trades_summary(self):
        comp = ContextCompressor(max_tokens=200)
        trades = [
            {"symbol": "AAPL", "pnl": 100},
            {"symbol": "GOOG", "pnl": -50},
            {"symbol": "MSFT", "pnl": 200},
        ]
        context = {
            "system_prompt": "Test",
            "trading_rules": "",
            "recent_trades": trades,
        }
        result = comp.compress(context)
        assert "blocks_included" in result

    def test_estimate_tokens(self):
        assert ContextCompressor._estimate_tokens_str("hello world") >= 2
        assert ContextCompressor._estimate_tokens_str("") == 0
