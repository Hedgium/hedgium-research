"""Flatten feature groups into a fixed numeric vector for ML."""

from __future__ import annotations

from analysis.ml.constants import FEATURE_COLUMNS


def _bool_float(value) -> float:
    if value is True:
        return 1.0
    if value is False:
        return 0.0
    return 0.0


def _num(value, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        f = float(value)
        if f != f:  # NaN
            return default
        return f
    except (TypeError, ValueError):
        return default


def build_feature_row(
    *,
    technical: dict | None,
    volatility: dict | None,
    fundamental: dict | None,
    corporate_risk: dict | None,
    market_context: dict | None = None,
) -> dict[str, float]:
    technical = technical or {}
    volatility = volatility or {}
    fundamental = fundamental or {}
    corporate_risk = corporate_risk or {}
    market_context = market_context or {}

    raw = {
        "rsi_14": _num(technical.get("rsi_14")),
        "macd": _num(technical.get("macd")),
        "macd_signal": _num(technical.get("macd_signal")),
        "macd_histogram": _num(technical.get("macd_histogram")),
        "macd_bullish_cross": _bool_float(technical.get("macd_bullish_cross")),
        "ema_20": _num(technical.get("ema_20")),
        "ema_50": _num(technical.get("ema_50")),
        "ema_200": _num(technical.get("ema_200")),
        "price_above_ema_20": _bool_float(technical.get("price_above_ema_20")),
        "price_above_ema_50": _bool_float(technical.get("price_above_ema_50")),
        "price_above_ema_200": _bool_float(technical.get("price_above_ema_200")),
        "adx_14": _num(technical.get("adx_14")),
        "atr_14": _num(technical.get("atr_14")),
        "volume_spike": _num(technical.get("volume_spike")),
        "vwap_proxy": _num(technical.get("vwap_proxy")),
        "historical_volatility_20d": _num(volatility.get("historical_volatility_20d")),
        "beta_252": _num(volatility.get("beta_252")),
        "sector_volatility_20d": _num(volatility.get("sector_volatility_20d")),
        "gap_count_60d": _num(volatility.get("gap_count_60d")),
        "gap_frequency_60d": _num(volatility.get("gap_frequency_60d")),
        "pe": _num(fundamental.get("pe")),
        "pb": _num(fundamental.get("pb")),
        "roe": _num(fundamental.get("roe")),
        "roce": _num(fundamental.get("roce")),
        "debt_equity": _num(fundamental.get("debt_equity")),
        "profit_growth_yoy": _num(fundamental.get("profit_growth_yoy")),
        "revenue_growth_yoy": _num(fundamental.get("revenue_growth_yoy")),
        "fundamental_data_available": _bool_float(fundamental.get("data_available")),
        "corp_active_event_count": _num(corporate_risk.get("active_event_count")),
        "corp_ceo_resigned": _bool_float(corporate_risk.get("ceo_resigned")),
        "corp_cfo_resigned": _bool_float(corporate_risk.get("cfo_resigned")),
        "corp_sebi_action": _bool_float(corporate_risk.get("sebi_action")),
        "corp_promoter_selling": _bool_float(corporate_risk.get("promoter_selling")),
        "fii_net": _num(market_context.get("fii_net")),
        "dii_net": _num(market_context.get("dii_net")),
        "sector_return_20d": _num(market_context.get("sector_return_20d")),
        "delivery_pct": _num(market_context.get("delivery_pct")),
    }
    return {col: raw.get(col, 0.0) for col in FEATURE_COLUMNS}


def row_to_vector(row: dict[str, float]) -> list[float]:
    return [row[col] for col in FEATURE_COLUMNS]
