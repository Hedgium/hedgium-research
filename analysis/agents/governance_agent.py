from __future__ import annotations

import json

from analysis.agents.base_agent import BaseAnalystAgent


class GovernanceAnalystAgent(BaseAnalystAgent):
    agent_name = "governance_analyst"

    def system_prompt(self) -> str:
        return (
            "You are a corporate governance analyst. "
            "Use only provided event/risk data and output strict JSON "
            "with keys: stance, confidence, bullets, risks, citations, raw_summary."
        )

    def user_prompt(self, context: dict) -> str:
        payload = context.get("governance_payload", {})
        return (
            "Assess governance quality and event risk impacts.\n"
            f"DATA:\n{json.dumps(payload, ensure_ascii=True)}"
        )

    def fallback(self, context: dict) -> dict:
        payload = context.get("governance_payload", {})
        risk_level = payload.get("risk_level", "LOW")
        warnings = payload.get("warnings", [])

        stance = "bullish" if risk_level == "LOW" else "neutral"
        if risk_level in {"HIGH", "CRITICAL"}:
            stance = "bearish"

        bullets = [f"Governance risk level is {risk_level}"]
        risks = warnings[:5]
        return {
            "stance": stance,
            "confidence": 0.65,
            "bullets": bullets,
            "risks": risks,
            "citations": ["analysis.risk_assessment", "market_data.corporate_events"],
            "raw_summary": "Deterministic fallback governance summary",
        }
