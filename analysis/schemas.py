from datetime import datetime
from decimal import Decimal
from typing import Any

from ninja import Schema


class HealthOut(Schema):
    status: str
    service: str
    timestamp: datetime


class ProbabilitiesOut(Schema):
    bullish: float
    bearish: float
    sideways: float


class NewsSummaryOut(Schema):
    positive: int
    neutral: int
    negative: int


class HoldingOutlookOut(Schema):
    horizon_days: str
    stance: str


class MarketDataOut(Schema):
    ohlcv_bars: int
    latest_date: str
    latest_close: float
    latest_delivery_pct: float | None = None
    sector_return_20d: float | None = None
    fii_net: float | None = None
    dii_net: float | None = None


class FeatureSummaryOut(Schema):
    as_of_date: str | None = None
    technical: dict | None = None
    volatility: dict | None = None
    fundamental: dict | None = None
    corporate_risk: dict | None = None


class AgentInsightsOut(Schema):
    provider: str
    enabled: bool
    elapsed_ms: int
    technical: dict
    fundamental: dict
    news: dict
    governance: dict
    master: dict


class ResearchReportOut(Schema):
    symbol: str
    company_name: str
    probabilities: ProbabilitiesOut
    confidence_score: float
    risk_level: str
    key_positive_factors: list[str]
    risk_factors: list[str]
    news_summary: NewsSummaryOut
    holding_outlook: HoldingOutlookOut
    generated_at: datetime
    status: str
    market_data: MarketDataOut | None = None
    features: FeatureSummaryOut | None = None
    model_version: str | None = None
    risk_score: float | None = None
    risk_rules: list[dict] | None = None
    agent_insights: AgentInsightsOut | None = None


def decimal_to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def build_stub_report(symbol_ticker: str, company_name: str) -> dict[str, Any]:
    """Placeholder report until ingestion, ML, and agents are wired."""
    return {
        "symbol": symbol_ticker,
        "company_name": company_name,
        "probabilities": {
            "bullish": 0.0,
            "bearish": 0.0,
            "sideways": 1.0,
        },
        "confidence_score": 0.0,
        "risk_level": "LOW",
        "key_positive_factors": [],
        "risk_factors": [],
        "news_summary": {"positive": 0, "neutral": 0, "negative": 0},
        "holding_outlook": {
            "horizon_days": "30-60",
            "stance": "Insufficient data",
        },
        "generated_at": datetime.now(),
        "status": "stub",
    }
