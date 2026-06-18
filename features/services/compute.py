"""Orchestrate feature snapshot computation and persistence."""

from __future__ import annotations

import logging
from datetime import date

import pandas as pd
from django.utils import timezone

from features.models import FeatureSnapshot
from features.services.corporate_risk import compute_corporate_risk_features
from features.services.data_loader import load_market_proxy_returns, load_ohlcv_dataframe
from features.services.fundamental import compute_fundamental_features
from features.services.technical import compute_technical_features
from features.services.volatility import compute_volatility_features
from symbols.models import Symbol

logger = logging.getLogger(__name__)

MIN_OHLCV_BARS = 30


def _upsert_snapshot(symbol: Symbol, as_of_date: date, group: str, features: dict) -> None:
    FeatureSnapshot.objects.update_or_create(
        symbol=symbol,
        as_of_date=as_of_date,
        feature_group=group,
        defaults={"features": features},
    )


def compute_features_for_symbol(
    symbol: Symbol,
    *,
    as_of_date: date | None = None,
    market_returns=None,
) -> dict:
    as_of_date = as_of_date or timezone.localdate()
    df = load_ohlcv_dataframe(symbol.id, min_rows=MIN_OHLCV_BARS)

    result = {
        "symbol": symbol.ticker,
        "status": "success",
        "groups": [],
    }

    if df is None:
        result["status"] = "skipped"
        result["reason"] = f"insufficient OHLCV (need {MIN_OHLCV_BARS}+ bars)"
        return result

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date

    latest_bar_date = df["date"].iloc[-1]
    snapshot_date = min(as_of_date, latest_bar_date)
    df = df[df["date"] <= snapshot_date].reset_index(drop=True)
    if len(df) < MIN_OHLCV_BARS:
        result["status"] = "skipped"
        result["reason"] = "insufficient OHLCV after date filter"
        return result

    technical = compute_technical_features(df)
    _upsert_snapshot(symbol, snapshot_date, FeatureSnapshot.FeatureGroup.TECHNICAL, technical)
    result["groups"].append("TECHNICAL")

    volatility = compute_volatility_features(df, symbol=symbol, market_returns=market_returns)
    _upsert_snapshot(symbol, snapshot_date, FeatureSnapshot.FeatureGroup.VOLATILITY, volatility)
    result["groups"].append("VOLATILITY")

    fundamental = compute_fundamental_features(symbol)
    _upsert_snapshot(symbol, snapshot_date, FeatureSnapshot.FeatureGroup.FUNDAMENTAL, fundamental)
    result["groups"].append("FUNDAMENTAL")

    corporate_risk = compute_corporate_risk_features(symbol)
    _upsert_snapshot(symbol, snapshot_date, FeatureSnapshot.FeatureGroup.CORPORATE_RISK, corporate_risk)
    result["groups"].append("CORPORATE_RISK")

    result["as_of_date"] = str(snapshot_date)
    return result


def compute_features_universe(
    *,
    index_name: str = "NIFTY50",
    as_of_date: date | None = None,
    tickers: list[str] | None = None,
) -> dict:
    symbols_qs = Symbol.objects.filter(
        is_active=True,
        exchange=Symbol.Exchange.NSE,
        index_memberships__index_name=index_name,
    ).select_related("company", "company__sector").distinct()

    if tickers:
        symbols_qs = symbols_qs.filter(ticker__in=tickers)

    symbols = list(symbols_qs.order_by("ticker"))
    if not symbols:
        return {"status": "error", "message": f"No symbols for index {index_name}"}

    market_returns = load_market_proxy_returns([s.id for s in symbols])

    results = []
    skipped = 0
    errors = []

    for symbol in symbols:
        try:
            row = compute_features_for_symbol(
                symbol,
                as_of_date=as_of_date,
                market_returns=market_returns,
            )
            results.append(row)
            if row.get("status") == "skipped":
                skipped += 1
        except Exception as exc:
            logger.exception("Feature computation failed for %s", symbol.ticker)
            errors.append({"symbol": symbol.ticker, "error": str(exc)})

    return {
        "status": "success" if not errors else "partial",
        "symbols_processed": len(results),
        "skipped": skipped,
        "errors": errors,
        "results": results,
    }
