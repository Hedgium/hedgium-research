from __future__ import annotations

import json

from analysis.agents.base_agent import BaseAnalystAgent


class FundamentalAnalystAgent(BaseAnalystAgent):
    agent_name = "fundamental_analyst"

    def system_prompt(self) -> str:
        return (
            "You are a fundamental analyst. "
            "Use only provided fundamental metrics. "
            "Return JSON keys: stance, confidence, bullets, risks, citations, raw_summary."
        )

    def user_prompt(self, context: dict) -> str:
        payload = context.get("fundamental_payload", {})
        return (
            "Assess balance sheet quality, profitability, and growth trends.\n"
            f"DATA:\n{json.dumps(payload, ensure_ascii=True)}"
        )

    def fallback(self, context: dict) -> dict:
        payload = context.get("fundamental_payload", {})
        if not payload.get("data_available"):
            return {
                "stance": "neutral",
                "confidence": 0.2,
                "bullets": ["Fundamental dataset is not yet available"],
                "risks": ["Fundamental confidence is low due to missing data"],
                "citations": ["features.fundamental"],
                "raw_summary": "Fallback: missing fundamental metrics",
            }

        bullets = []
        risks = []
        if (payload.get("roe") or 0) > 15:
            bullets.append("ROE is above 15%")
        if (payload.get("profit_growth_yoy") or 0) > 10:
            bullets.append("Profit growth is positive and strong")
        if (payload.get("debt_equity") or 0) > 1.5:
            risks.append("Debt-to-equity appears elevated")

        return {
            "stance": "bullish" if bullets else "neutral",
            "confidence": 0.6 if bullets else 0.45,
            "bullets": bullets[:5],
            "risks": risks[:5],
            "citations": ["features.fundamental"],
            "raw_summary": "Deterministic fallback fundamental summary",
        }
