from __future__ import annotations

from django.conf import settings

from analysis.agents.llm.base import BaseLLMClient, LLMClientError


def get_llm_client(provider: str | None = None) -> BaseLLMClient:
    provider = (provider or settings.AGENT_PROVIDER or "openai").lower()
    timeout = settings.AGENT_TIMEOUT_SEC
    max_tokens = settings.AGENT_MAX_TOKENS

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise LLMClientError("OPENAI_API_KEY not configured")
        from analysis.agents.llm.openai_client import OpenAIClient

        return OpenAIClient(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            timeout_sec=timeout,
            max_tokens=max_tokens,
        )

    if provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise LLMClientError("ANTHROPIC_API_KEY not configured")
        from analysis.agents.llm.anthropic_client import AnthropicClient

        return AnthropicClient(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
            timeout_sec=timeout,
            max_tokens=max_tokens,
        )

    raise LLMClientError(f"Unsupported AGENT_PROVIDER: {provider}")
