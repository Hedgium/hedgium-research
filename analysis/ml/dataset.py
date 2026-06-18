"""Build labeled training dataset from historical OHLCV."""

from __future__ import annotations

import logging
from datetime import date

import pandas as pd

from analysis.ml.constants import (
    BEARISH_THRESHOLD,
    BULLISH_THRESHOLD,
    CLASS_BEARISH,
    CLASS_BULLISH,
    CLASS_SIDEWAYS,
    FORWARD_DAYS,
)
from analysis.ml.feature_vector import build_feature_row, row_to_vector
from features.services.corporate_risk import compute_corporate_risk_features
from features.services.data_loader import load_market_proxy_returns, load_ohlcv_dataframe
from features.services.fundamental import compute_fundamental_features
from features.services.technical import compute_technical_features
from features.services.volatility import compute_volatility_features
from symbols.models import Symbol

logger = logging.getLogger(__name__)

MIN_HISTORY = 60


def classify_forward_return(fwd_return: float) -> int:
    if fwd_return > BULLISH_THRESHOLD:
        return CLASS_BULLISH
    if fwd_return < BEARISH_THRESHOLD:
        return CLASS_BEARISH
    return CLASS_SIDEWAYS


def _build_market_context(symbol: Symbol) -> dict:
    from market_data.models import DeliveryDaily, FIIDIIActivity, SectorPerformance

    ctx: dict = {}
    latest_fii = FIIDIIActivity.objects.order_by("-date").first()
    if latest_fii:
        ctx["fii_net"] = float(latest_fii.fii_net) if latest_fii.fii_net is not None else None
        ctx["dii_net"] = float(latest_fii.dii_net) if latest_fii.dii_net is not None else None

    sector = symbol.company.sector
    if sector:
        perf = SectorPerformance.objects.filter(sector=sector).order_by("-date").first()
        if perf and perf.return_20d is not None:
            ctx["sector_return_20d"] = float(perf.return_20d)

    delivery = (
        DeliveryDaily.objects.filter(symbol=symbol).order_by("-date").values_list("delivery_pct", flat=True).first()
    )
    if delivery is not None:
        ctx["delivery_pct"] = float(delivery)
    return ctx


def build_symbol_training_rows(
    symbol: Symbol,
    *,
    market_returns: pd.Series | None,
    sample_step: int = 5,
    max_rows_per_symbol: int | None = 400,
) -> list[dict]:
    df = load_ohlcv_dataframe(symbol.id, min_rows=MIN_HISTORY + FORWARD_DAYS + 1)
    if df is None:
        return []

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    close = df["close"].astype(float)

    fundamental = compute_fundamental_features(symbol)
    market_context = _build_market_context(symbol)

    rows: list[dict] = []
    last_index = len(df) - FORWARD_DAYS - 1
    indices = range(MIN_HISTORY, last_index + 1, sample_step)

    for i in indices:
        window = df.iloc[: i + 1].reset_index(drop=True)
        as_of = window["date"].iloc[-1]

        technical = compute_technical_features(window)
        volatility = compute_volatility_features(window, symbol=symbol, market_returns=market_returns)
        corporate_risk = compute_corporate_risk_features(symbol)

        fwd_return = float(close.iloc[i + FORWARD_DAYS] / close.iloc[i] - 1.0)
        label = classify_forward_return(fwd_return)

        feature_row = build_feature_row(
            technical=technical,
            volatility=volatility,
            fundamental=fundamental,
            corporate_risk=corporate_risk,
            market_context=market_context,
        )

        rows.append(
            {
                "symbol": symbol.ticker,
                "as_of_date": as_of,
                "label": label,
                "fwd_return": fwd_return,
                "features": feature_row,
                "vector": row_to_vector(feature_row),
            }
        )

        if max_rows_per_symbol and len(rows) >= max_rows_per_symbol:
            break

    return rows


def build_training_dataset(
    *,
    index_name: str = "NIFTY50",
    sample_step: int = 5,
    max_rows_per_symbol: int | None = 400,
) -> tuple[list[list[float]], list[int], list[date], list[str]]:
    symbols = list(
        Symbol.objects.filter(
            is_active=True,
            exchange=Symbol.Exchange.NSE,
            index_memberships__index_name=index_name,
        )
        .select_related("company", "company__sector")
        .distinct()
        .order_by("ticker")
    )
    market_returns = load_market_proxy_returns([s.id for s in symbols])

    vectors: list[list[float]] = []
    labels: list[int] = []
    dates: list[date] = []
    tickers: list[str] = []

    for symbol in symbols:
        try:
            symbol_rows = build_symbol_training_rows(
                symbol,
                market_returns=market_returns,
                sample_step=sample_step,
                max_rows_per_symbol=max_rows_per_symbol,
            )
            for row in symbol_rows:
                vectors.append(row["vector"])
                labels.append(row["label"])
                dates.append(row["as_of_date"])
                tickers.append(row["symbol"])
        except Exception:
            logger.exception("Failed building training rows for %s", symbol.ticker)

    return vectors, labels, dates, tickers
