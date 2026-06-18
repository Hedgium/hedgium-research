from __future__ import annotations

from datetime import timedelta
from time import perf_counter
from typing import Any

from django.conf import settings
from django.utils import timezone
import logging

from analysis.agents.fundamental_agent import FundamentalAnalystAgent
from analysis.agents.governance_agent import GovernanceAnalystAgent
from analysis.agents.master_agent import MasterDecisionAgent
from analysis.agents.news_agent import NewsAnalystAgent
from analysis.agents.technical_agent import TechnicalAnalystAgent
from market_data.models import NewsArticle

logger = logging.getLogger(__name__)


def _news_payload(symbol) -> dict[str, Any]:
    since = timezone.now() - timedelta(days=30)
    qs = NewsArticle.objects.filter(symbol=symbol, published_at__gte=since).order_by("-published_at")
    counts = {
        "positive": qs.filter(sentiment=NewsArticle.Sentiment.POSITIVE).count(),
        "neutral": qs.filter(sentiment=NewsArticle.Sentiment.NEUTRAL).count(),
        "negative": qs.filter(sentiment=NewsArticle.Sentiment.NEGATIVE).count(),
    }
    latest = list(
        qs.values("title", "source", "sentiment", "published_at", "summary", "url")[:10]
    )
    for row in latest:
        if row.get("published_at") is not None:
            row["published_at"] = row["published_at"].isoformat()
    return {"counts": counts, "latest_articles": latest}


def run_specialized_agents(
    *,
    symbol,
    company_name: str,
    as_of_date: str,
    feature_map: dict[str, Any],
    predictions: dict[str, Any],
    risk: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute specialist analysts and master decision synthesis.
    Returns structured dict, always with deterministic fallback values.
    """
    provider = settings.AGENT_PROVIDER
    enabled = bool(settings.AGENT_ENABLE)
    news_payload = _news_payload(symbol)

    technical_payload = {
        **(feature_map.get("TECHNICAL") or {}),
        **(feature_map.get("VOLATILITY") or {}),
    }
    fundamental_payload = feature_map.get("FUNDAMENTAL") or {}
    governance_payload = {
        **(feature_map.get("CORPORATE_RISK") or {}),
        "risk_level": risk.get("risk_level", "LOW"),
        "warnings": risk.get("warnings", []),
    }

    context_base = {
        "symbol": symbol.ticker,
        "company_name": company_name,
        "as_of_date": as_of_date,
    }

    t0 = perf_counter()
    if enabled:
        technical = TechnicalAnalystAgent(provider=provider).analyze(
            {**context_base, "technical_payload": technical_payload}
        )
        fundamental = FundamentalAnalystAgent(provider=provider).analyze(
            {**context_base, "fundamental_payload": fundamental_payload}
        )
        news = NewsAnalystAgent(provider=provider).analyze(
            {**context_base, "news_payload": news_payload}
        )
        governance = GovernanceAnalystAgent(provider=provider).analyze(
            {**context_base, "governance_payload": governance_payload}
        )
        master = MasterDecisionAgent(provider=provider).analyze(
            {
                **context_base,
                "predictions": predictions,
                "risk": risk,
                "technical": technical,
                "fundamental": fundamental,
                "news": news,
                "governance": governance,
                "news_counts": news_payload.get("counts", {}),
            }
        )
    else:
        technical = TechnicalAnalystAgent(provider=provider).fallback(
            {**context_base, "technical_payload": technical_payload}
        )
        fundamental = FundamentalAnalystAgent(provider=provider).fallback(
            {**context_base, "fundamental_payload": fundamental_payload}
        )
        news = NewsAnalystAgent(provider=provider).fallback(
            {**context_base, "news_payload": news_payload}
        )
        governance = GovernanceAnalystAgent(provider=provider).fallback(
            {**context_base, "governance_payload": governance_payload}
        )
        master = MasterDecisionAgent(provider=provider).fallback(
            {
                **context_base,
                "predictions": predictions,
                "risk": risk,
                "technical": technical,
                "fundamental": fundamental,
                "news": news,
                "governance": governance,
                "news_counts": news_payload.get("counts", {}),
            }
        )

    elapsed_ms = int((perf_counter() - t0) * 1000)
    fallback_used = any(
        isinstance(block, dict) and "fallback" in (block.get("raw_summary", "").lower())
        for block in (technical, fundamental, news, governance, master)
    )
    logger.info(
        "agent_orchestration_complete symbol=%s provider=%s enabled=%s elapsed_ms=%s fallback_used=%s",
        symbol.ticker,
        provider,
        enabled,
        elapsed_ms,
        fallback_used,
    )
    return {
        "provider": provider,
        "enabled": enabled,
        "elapsed_ms": elapsed_ms,
        "fallback_used": fallback_used,
        "technical": technical,
        "fundamental": fundamental,
        "news": news,
        "governance": governance,
        "master": master,
        "news_counts": news_payload.get("counts", {"positive": 0, "neutral": 0, "negative": 0}),
    }
