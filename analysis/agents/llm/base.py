from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


class LLMClientError(RuntimeError):
    pass


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, Any] | None = None


class BaseLLMClient:
    provider_name = "base"

    def __init__(self, *, model: str, timeout_sec: int = 30, max_tokens: int = 1200):
        self.model = model
        self.timeout_sec = timeout_sec
        self.max_tokens = max_tokens

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        raise NotImplementedError

    @staticmethod
    def parse_json_object(text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        return json.loads(text)
