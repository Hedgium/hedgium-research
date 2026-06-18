"""Load OHLCV history into pandas for feature computation."""

from __future__ import annotations

import pandas as pd

from market_data.models import OHLCVDaily


def load_ohlcv_dataframe(symbol_id: int, *, min_rows: int = 30) -> pd.DataFrame | None:
    rows = (
        OHLCVDaily.objects.filter(symbol_id=symbol_id)
        .order_by("date")
        .values_list("date", "open", "high", "low", "close", "volume")
    )
    if len(rows) < min_rows:
        return None

    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    if len(df) < min_rows:
        return None
    return df


def load_market_proxy_returns(symbol_ids: list[int], window: int = 260) -> pd.Series | None:
    """
    Equal-weighted daily log-return proxy across symbols (NIFTY 50 basket).
    Index-aligned by date.
    """
    if not symbol_ids:
        return None

    frames = []
    for sid in symbol_ids:
        df = load_ohlcv_dataframe(sid, min_rows=5)
        if df is None or len(df) < 2:
            continue
        part = df[["date", "close"]].copy()
        part["daily_return"] = part["close"].pct_change()
        part = part.rename(columns={"daily_return": f"ret_{sid}"})
        frames.append(part[["date", f"ret_{sid}"]])

    if not frames:
        return None

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="date", how="outer")

    merged = merged.sort_values("date").tail(window + 1)
    ret_cols = [c for c in merged.columns if c.startswith("ret_")]
    market_ret = merged[ret_cols].mean(axis=1, skipna=True)
    market_ret.index = merged["date"]
    return market_ret.dropna()
