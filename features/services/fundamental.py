"""Fundamental features — from FundamentalMetric rows when available."""

from __future__ import annotations

import math

from features.models import FundamentalMetric


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def compute_fundamental_features(symbol) -> dict:
    latest = (
        FundamentalMetric.objects.filter(symbol=symbol)
        .order_by("-period_end")
        .first()
    )
    if not latest:
        return {
            "data_available": False,
            "pe": None,
            "pb": None,
            "roe": None,
            "roce": None,
            "debt_equity": None,
            "profit_growth_yoy": None,
            "revenue_growth_yoy": None,
        }

    return {
        "data_available": True,
        "period_end": str(latest.period_end),
        "pe": _safe_float(latest.pe),
        "pb": _safe_float(latest.pb),
        "roe": _safe_float(latest.roe),
        "roce": _safe_float(latest.roce),
        "debt_equity": _safe_float(latest.debt_equity),
        "profit_growth_yoy": _safe_float(latest.profit_growth_yoy),
        "revenue_growth_yoy": _safe_float(latest.revenue_growth_yoy),
    }
