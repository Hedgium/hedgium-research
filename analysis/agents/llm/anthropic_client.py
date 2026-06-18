from __future__ import annotations

from anthropic import Anthropic

from analysis.agents.llm.base import BaseLLMClient, LLMClientError, LLMResponse


class AnthropicClient(BaseLLMClient):
    provider_name = "anthropic"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_sec: int = 30,
        max_tokens: int = 1200,
    ):
        super().__init__(model=model, timeout_sec=timeout_sec, max_tokens=max_tokens)
        self.client = Anthropic(api_key=api_key, timeout=timeout_sec)

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.2,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as exc:  # pragma: no cover
            raise LLMClientError(f"Anthropic request failed: {exc}") from exc

        text_chunks = []
        for block in getattr(resp, "content", []) or []:
            if getattr(block, "type", "") == "text":
                text_chunks.append(getattr(block, "text", ""))
        content = "".join(text_chunks).strip() or "{}"
        usage = getattr(resp, "usage", None)
        usage_dict = None
        if usage:
            usage_dict = {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
            }
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider_name,
            usage=usage_dict,
        )
