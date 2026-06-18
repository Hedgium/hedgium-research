"""OHLCV ingestion via Kite historical API."""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from market_data.models import OHLCVDaily
from symbols.models import Symbol

from .instruments import sync_nse_equity_tokens
from .kite_client import fetch_historical_daily, get_kite_client

logger = logging.getLogger(__name__)


def _decimal(value) -> Decimal:
    return Decimal(str(value))


def _upsert_ohlcv_rows(symbol: Symbol, candles: list[dict]) -> int:
    if not candles:
        return 0

    rows = [
        OHLCVDaily(
            symbol=symbol,
            date=candle["date"].date() if hasattr(candle["date"], "date") else candle["date"],
            open=_decimal(candle["open"]),
            high=_decimal(candle["high"]),
            low=_decimal(candle["low"]),
            close=_decimal(candle["close"]),
            volume=int(candle.get("volume") or 0),
        )
        for candle in candles
    ]

    OHLCVDaily.objects.bulk_create(
        rows,
        update_conflicts=True,
        update_fields=["open", "high", "low", "close", "volume"],
        unique_fields=["symbol", "date"],
    )
    return len(rows)


def ingest_ohlcv_for_symbol(
    symbol: Symbol,
    *,
    from_date: date,
    to_date: date,
    kite=None,
) -> dict:
    if not symbol.instrument_token:
        return {"symbol": symbol.ticker, "status": "skipped", "reason": "no instrument_token"}

    client = kite or get_kite_client()
    candles = fetch_historical_daily(
        client,
        int(symbol.instrument_token),
        from_date,
        to_date,
    )
    count = _upsert_ohlcv_rows(symbol, candles)
    return {"symbol": symbol.ticker, "status": "success", "rows": count}


def ingest_ohlcv_universe(
    *,
    index_name: str = "NIFTY50",
    days: int | None = None,
    backfill_years: int | None = None,
    tickers: list[str] | None = None,
    sync_tokens: bool = True,
) -> dict:
    """
    Ingest daily OHLCV for index constituents (default NIFTY 50).
    Use ``days`` for incremental daily runs or ``backfill_years`` for history.
    """
    to_date = timezone.localdate()
    if backfill_years:
        from_date = to_date - timedelta(days=backfill_years * 365)
    elif days:
        from_date = to_date - timedelta(days=days)
    else:
        from_date = to_date - timedelta(days=5)

    if sync_tokens:
        sync_result = sync_nse_equity_tokens()
        logger.info("Instrument token sync: %s", sync_result)

    symbols_qs = Symbol.objects.filter(
        is_active=True,
        exchange=Symbol.Exchange.NSE,
        index_memberships__index_name=index_name,
    ).distinct()
    if tickers:
        symbols_qs = symbols_qs.filter(ticker__in=tickers)

    symbols = list(symbols_qs.order_by("ticker"))
    if not symbols:
        return {"status": "error", "message": f"No symbols found for index {index_name}"}

    kite = get_kite_client()
    delay = getattr(settings, "KITE_REQUEST_DELAY_SEC", 0.35)

    results = []
    errors = []
    total_rows = 0

    for symbol in symbols:
        try:
            result = ingest_ohlcv_for_symbol(
                symbol,
                from_date=from_date,
                to_date=to_date,
                kite=kite,
            )
            results.append(result)
            total_rows += result.get("rows", 0)
        except Exception as exc:
            logger.exception("OHLCV ingest failed for %s", symbol.ticker)
            errors.append({"symbol": symbol.ticker, "error": str(exc)})
        if delay > 0:
            time.sleep(delay)

    return {
        "status": "success" if not errors else "partial",
        "from_date": str(from_date),
        "to_date": str(to_date),
        "symbols_processed": len(results),
        "total_rows": total_rows,
        "errors": errors,
        "results": results,
    }
