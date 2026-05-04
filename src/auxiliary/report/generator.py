from __future__ import annotations

import json
import csv
import io
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.constants import D, ZERO


class ReportGenerator:
    def generate_performance_report(
        self,
        ai_player_id: str,
        initial_capital: Decimal,
        final_capital: Decimal,
        daily_returns: list[Decimal],
        trade_count: int = 0,
        win_count: int = 0,
        loan_cost: Decimal = ZERO,
    ) -> dict[str, Any]:
        return_rate = (final_capital - initial_capital) / initial_capital if initial_capital > ZERO else ZERO
        max_drawdown = self._calculate_max_drawdown(daily_returns)
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        win_rate = D(str(win_count)) / D(str(trade_count)) if trade_count > 0 else ZERO
        return {
            "ai_player_id": ai_player_id,
            "initial_capital": str(initial_capital),
            "final_capital": str(final_capital),
            "return_rate": str(return_rate.quantize(D("0.0001"))),
            "max_drawdown": str(max_drawdown.quantize(D("0.0001"))),
            "sharpe_ratio": str(sharpe_ratio.quantize(D("0.01"))),
            "trade_count": trade_count,
            "win_rate": str(win_rate.quantize(D("0.0001"))),
            "loan_cost": str(loan_cost),
        }

    @staticmethod
    def _calculate_max_drawdown(daily_returns: list[Decimal]) -> Decimal:
        if not daily_returns:
            return ZERO
        peak = ZERO
        max_dd = ZERO
        cumulative = D("1")
        for ret in daily_returns:
            cumulative *= (D("1") + ret)
            if cumulative > peak:
                peak = cumulative
            dd = (peak - cumulative) / peak if peak > ZERO else ZERO
            if dd > max_dd:
                max_dd = dd
        return max_dd

    @staticmethod
    def _calculate_sharpe_ratio(daily_returns: list[Decimal], risk_free_rate: Decimal = ZERO) -> Decimal:
        if len(daily_returns) < 2:
            return ZERO
        avg = sum(daily_returns) / len(daily_returns)
        excess = avg - risk_free_rate / D("252")
        variance = sum((r - avg) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        if variance <= ZERO:
            return ZERO
        from decimal import Decimal as Dec
        std = variance.sqrt()
        return (excess / std) * D("252").sqrt() if std > ZERO else ZERO

    def export_csv(self, data: list[dict], filepath: Path) -> None:
        if not data:
            return
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    def export_json(self, data: Any, filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, default=str, indent=2, ensure_ascii=False)

    def export_html(self, title: str, data: list[dict], filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        html = f"<!DOCTYPE html><html><head><title>{title}</title></head><body><h1>{title}</h1>"
        if data:
            html += "<table border='1'><tr>"
            for key in data[0].keys():
                html += f"<th>{key}</th>"
            html += "</tr>"
            for row in data:
                html += "<tr>"
                for val in row.values():
                    html += f"<td>{val}</td>"
                html += "</tr>"
            html += "</table>"
        html += "</body></html>"
        filepath.write_text(html, encoding="utf-8")
