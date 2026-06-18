from __future__ import annotations

import json

from analysis.agents.base_agent import BaseAnalystAgent


class NewsAnalystAgent(BaseAnalystAgent):
    agent_name = "news_analyst"

    def system_prompt(self) -> str:
        return (
            "You are a news analyst for equities. "
            "Summarize sentiment and themes from provided article metadata only. "
            "Return JSON keys: stance, confidence, bullets, risks, citations, raw_summary."
        )

    def user_prompt(self, context: dict) -> str:
        payload = context.get("news_payload", {})
        return (
            "Generate concise news view for 30-60 day horizon from these inputs only.\n"
            f"DATA:\n{json.dumps(payload, ensure_ascii=True)}"
        )

    def fallback(self, context: dict) -> dict:
        payload = context.get("news_payload", {})
        counts = payload.get("counts", {})
        pos = counts.get("positive", 0)
        neg = counts.get("negative", 0)
        neu = counts.get("neutral", 0)

        stance = "neutral"
        if pos > neg:
            stance = "bullish"
        elif neg > pos:
            stance = "bearish"

        bullets = [f"News sentiment mix: +{pos} / ~{neu} / -{neg}"]
        risks = []
        if neg > pos:
            risks.append("Negative news outweighs positive coverage")

        return {
            "stance": stance,
            "confidence": 0.55,
            "bullets": bullets,
            "risks": risks,
            "citations": ["market_data.news_articles"],
            "raw_summary": "Deterministic fallback news summary",
        }
