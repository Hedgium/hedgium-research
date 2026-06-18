from __future__ import annotations

import json
from typing import Any

from analysis.agents.base_agent import BaseAnalystAgent


class TechnicalAnalystAgent(BaseAnalystAgent):
    agent_name = "technical_analyst"

    def system_prompt(self) -> str:
        return (
            "You are a technical analyst. "
            "Use only provided technical + volatility values. "
            "Return strict JSON with keys: stance, confidence, bullets, risks, citations, raw_summary."
        )

    def user_prompt(self, context: dict[str, Any]) -> str:
        payload = context.get("technical_payload", {})
        return (
            "Analyze momentum and trend for next 30-60 days from this data.\n"
            "Do not infer unavailable metrics.\n"
            f"DATA:\n{json.dumps(payload, ensure_ascii=True)}"
        )

    def fallback(self, context: dict[str, Any]) -> dict[str, Any]:
        payload = context.get("technical_payload", {})
        bullets: list[str] = []
        risks: list[str] = []
        if payload.get("macd_bullish_cross"):
            bullets.append("MACD shows a bullish crossover")
        if payload.get("price_above_ema_50"):
            bullets.append("Price is above 50-day EMA")
        if (payload.get("volume_spike") or 0) > 1.5:
            bullets.append("Volume is elevated versus 20-day baseline")
        if (payload.get("adx_14") or 0) < 18:
            risks.append("Trend strength appears weak (low ADX)")

        return {
            "stance": "bullish" if payload.get("macd_bullish_cross") else "neutral",
            "confidence": 0.55 if payload.get("macd_bullish_cross") else 0.45,
            "bullets": bullets[:5],
            "risks": risks[:5],
            "citations": ["features.technical", "features.volatility"],
            "raw_summary": "Deterministic fallback technical summary",
        }
