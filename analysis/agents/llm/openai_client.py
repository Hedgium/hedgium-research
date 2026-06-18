from __future__ import annotations

from openai import OpenAI

from analysis.agents.llm.base import BaseLLMClient, LLMClientError, LLMResponse


class OpenAIClient(BaseLLMClient):
    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_sec: int = 30,
        max_tokens: int = 1200,
    ):
        super().__init__(model=model, timeout_sec=timeout_sec, max_tokens=max_tokens)
        self.client = OpenAI(api_key=api_key, timeout=timeout_sec)

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:  # pragma: no cover
            raise LLMClientError(f"OpenAI request failed: {exc}") from exc

        content = resp.choices[0].message.content if resp.choices else ""
        return LLMResponse(
            content=content or "{}",
            model=self.model,
            provider=self.provider_name,
            usage=(resp.usage.model_dump() if getattr(resp, "usage", None) else None),
        )
