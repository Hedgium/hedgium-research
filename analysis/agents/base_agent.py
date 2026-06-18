from __future__ import annotations

import json
from typing import Any

from analysis.agents.llm.base import LLMClientError
from analysis.agents.llm.factory import get_llm_client


class BaseAnalystAgent:
    agent_name = "base_analyst"

    def __init__(self, *, provider: str | None = None):
        self.provider = provider

    def system_prompt(self) -> str:
        return (
            "You are a financial analysis assistant. "
            "Use only provided data. Do not invent numbers. "
            "Return strict JSON."
        )

    def user_prompt(self, context: dict[str, Any]) -> str:
        return json.dumps(context, ensure_ascii=True)

    def fallback(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "stance": "neutral",
            "confidence": 0.0,
            "bullets": [],
            "risks": [],
            "citations": [],
            "raw_summary": f"{self.agent_name} fallback: LLM unavailable",
        }

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        try:
            client = get_llm_client(self.provider)
            response = client.complete_json(
                system_prompt=self.system_prompt(),
                user_prompt=self.user_prompt(context),
            )
            parsed = client.parse_json_object(response.content)
            parsed.setdefault("raw_summary", "")
            return parsed
        except (LLMClientError, ValueError, TypeError, json.JSONDecodeError):
            return self.fallback(context)
