"""Volatility and market-relative features."""

from __future__ import annotations

import math
from datetime import timedelta

import numpy as np
import pandas as pd
from django.utils import timezone

from market_data.models import SectorPerformance
from symbols.models import Symbol

from .data_loader import load_ohlcv_dataframe, load_market_proxy_returns

TRADING_DAYS_PER_YEAR = 252
GAP_THRESHOLD_PCT = 1.0
GAP_LOOKBACK_DAYS = 60


def _safe_float(value) -> float | None:
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return float(value)


def _log_returns(close: pd.Series) -> pd.Series:
    return np.log(close / close.shift(1))


def compute_volatility_features(
    df: pd.DataFrame,
    *,
    symbol: Symbol,
    market_returns: pd.Series | None,
) -> dict:
    close = df["close"]
    open_ = df["open"]
    log_ret = _log_returns(close)

    # 20-day historical volatility (annualized)
    hist_vol_20 = log_ret.rolling(20).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    hist_vol_20_val = _safe_float(hist_vol_20.iloc[-1])

    # Beta vs equal-weight market proxy (252d rolling)
    beta_252 = None
    if market_returns is not None and len(market_returns) >= 30:
        stock_ret = close.pct_change()
        stock_ret.index = df["date"]
        aligned = pd.concat(
            [stock_ret.rename("stock"), market_returns.rename("market")],
            axis=1,
            join="inner",
        ).dropna()
        if len(aligned) >= 30:
            window = aligned.tail(min(252, len(aligned)))
            stock_var = window["stock"].var()
            market_var = window["market"].var()
            if market_var and market_var > 0 and stock_var is not None:
                beta_252 = _safe_float(window["stock"].cov(window["market"]) / market_var)

    # Sector volatility from pre-computed sector performance or OHLCV dispersion
    sector_vol_20 = None
    sector = symbol.company.sector
    if sector:
        perf_rows = list(
            SectorPerformance.objects.filter(sector=sector)
            .order_by("-date")
            .values_list("return_1d", flat=True)[:20]
        )
        if len(perf_rows) >= 5:
            sector_vol_20 = _safe_float(pd.Series([float(x) for x in perf_rows]).std())

    # Gap frequency in last 60 sessions
    prev_close = close.shift(1)
    gap_pct = ((open_ - prev_close).abs() / prev_close.replace(0, pd.NA)) * 100
    recent = gap_pct.tail(GAP_LOOKBACK_DAYS)
    gap_count = int((recent > GAP_THRESHOLD_PCT).sum())
    gap_frequency = _safe_float(gap_count / max(len(recent.dropna()), 1))

    return {
        "historical_volatility_20d": hist_vol_20_val,
        "beta_252": beta_252,
        "sector_volatility_20d": sector_vol_20,
        "gap_count_60d": gap_count,
        "gap_frequency_60d": gap_frequency,
    }
