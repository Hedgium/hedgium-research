from __future__ import annotations

import json

from analysis.agents.base_agent import BaseAnalystAgent


class MasterDecisionAgent(BaseAnalystAgent):
    agent_name = "master_decision_agent"

    def system_prompt(self) -> str:
        return (
            "You are the master investment synthesis agent. "
            "Combine specialist outputs, ML probabilities, and deterministic risk. "
            "Return strict JSON with keys: key_positive_factors, risk_factors, "
            "holding_outlook, news_summary, rationale."
        )

    def user_prompt(self, context: dict) -> str:
        return (
            "Synthesize final 30-60 day view from these inputs only.\n"
            f"DATA:\n{json.dumps(context, ensure_ascii=True)}"
        )

    def fallback(self, context: dict) -> dict:
        predictions = context.get("predictions", {})
        risk = context.get("risk", {})
        tech = context.get("technical", {})
        fund = context.get("fundamental", {})
        news = context.get("news", {})
        gov = context.get("governance", {})

        positives = []
        positives.extend((tech.get("bullets") or [])[:2])
        positives.extend((fund.get("bullets") or [])[:2])
        positives = positives[:5]

        risk_factors = []
        risk_factors.extend((gov.get("risks") or [])[:3])
        risk_factors.extend((risk.get("warnings") or [])[:3])
        risk_factors = risk_factors[:6]

        outlook = {
            "horizon_days": "30-60",
            "stance": "Moderately Bullish" if (predictions.get("bullish", 0) >= 0.6) else "Neutral / Mixed",
        }
        return {
            "key_positive_factors": positives,
            "risk_factors": risk_factors,
            "holding_outlook": outlook,
            "news_summary": context.get("news_counts", {"positive": 0, "neutral": 0, "negative": 0}),
            "rationale": "Fallback synthesis from deterministic summaries",
        }
