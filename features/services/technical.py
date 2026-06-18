"""Technical indicator features — pre-computed, not LLM."""

from __future__ import annotations

import math

import pandas as pd
import pandas_ta as ta


def _safe_float(value) -> float | None:
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return float(value)


def compute_technical_features(df: pd.DataFrame) -> dict:
    """
    Compute latest technical feature values from OHLCV history.
    Requires ~30+ bars; EMA200 needs 200+ for full accuracy.
    """
    work = df.copy()
    close = work["close"]
    high = work["high"]
    low = work["low"]
    volume = work["volume"]

    # RSI
    work["rsi_14"] = ta.rsi(close, length=14)

    # MACD
    macd = ta.macd(close, fast=12, slow=26, signal=9)
    if macd is not None and not macd.empty:
        work = pd.concat([work, macd], axis=1)

    # EMAs
    work["ema_20"] = ta.ema(close, length=20)
    work["ema_50"] = ta.ema(close, length=50)
    work["ema_200"] = ta.ema(close, length=200)

    # ADX
    adx = ta.adx(high, low, close, length=14)
    if adx is not None and not adx.empty:
        work = pd.concat([work, adx], axis=1)

    # ATR
    work["atr_14"] = ta.atr(high, low, close, length=14)

    # Volume spike vs 20-day average
    vol_sma_20 = volume.rolling(20).mean()
    work["volume_spike"] = volume / vol_sma_20

    # VWAP proxy (daily typical price cumulative)
    typical_price = (high + low + close) / 3.0
    cum_vol = volume.cumsum()
    work["vwap_proxy"] = (typical_price * volume).cumsum() / cum_vol.replace(0, pd.NA)

    latest = work.iloc[-1]
    prev = work.iloc[-2] if len(work) > 1 else latest

    macd_line_col = next((c for c in work.columns if c.startswith("MACD_")), None)
    macd_signal_col = next((c for c in work.columns if c.startswith("MACDs_")), None)
    macd_hist_col = next((c for c in work.columns if c.startswith("MACDh_")), None)
    adx_col = next((c for c in work.columns if c.startswith("ADX_") and not c.startswith("ADXR_")), None)

    close_val = _safe_float(latest["close"])
    ema_20 = _safe_float(latest.get("ema_20"))
    ema_50 = _safe_float(latest.get("ema_50"))
    ema_200 = _safe_float(latest.get("ema_200"))

    return {
        "rsi_14": _safe_float(latest.get("rsi_14")),
        "macd": _safe_float(latest.get(macd_line_col)) if macd_line_col else None,
        "macd_signal": _safe_float(latest.get(macd_signal_col)) if macd_signal_col else None,
        "macd_histogram": _safe_float(latest.get(macd_hist_col)) if macd_hist_col else None,
        "macd_bullish_cross": bool(
            macd_line_col
            and macd_signal_col
            and _safe_float(prev.get(macd_line_col)) is not None
            and _safe_float(prev.get(macd_signal_col)) is not None
            and _safe_float(prev.get(macd_line_col)) <= _safe_float(prev.get(macd_signal_col))
            and _safe_float(latest.get(macd_line_col)) > _safe_float(latest.get(macd_signal_col))
        ),
        "ema_20": ema_20,
        "ema_50": ema_50,
        "ema_200": ema_200,
        "price_above_ema_20": close_val > ema_20 if close_val and ema_20 else None,
        "price_above_ema_50": close_val > ema_50 if close_val and ema_50 else None,
        "price_above_ema_200": close_val > ema_200 if close_val and ema_200 else None,
        "adx_14": _safe_float(latest.get(adx_col)) if adx_col else None,
        "atr_14": _safe_float(latest.get("atr_14")),
        "volume_spike": _safe_float(latest.get("volume_spike")),
        "vwap_proxy": _safe_float(latest.get("vwap_proxy")),
        "close": close_val,
    }
