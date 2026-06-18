"""Sync Zerodha instrument tokens onto research Symbol rows."""

from __future__ import annotations

import csv
import logging
from io import StringIO

from symbols.models import Symbol

from .kite_client import download_instruments_csv

logger = logging.getLogger(__name__)


def sync_nse_equity_tokens(*, tickers: list[str] | None = None) -> dict:
    """
    Map NSE EQ instrument_token from Kite instruments CSV.
    Returns counts of updated / missing symbols.
    """
    csv_text = download_instruments_csv()
    reader = csv.DictReader(StringIO(csv_text))

    token_by_ticker: dict[str, int] = {}
    for row in reader:
        if row.get("exchange") != "NSE":
            continue
        if row.get("instrument_type") != "EQ":
            continue
        ticker = (row.get("tradingsymbol") or "").strip()
        if not ticker:
            continue
        try:
            token_by_ticker[ticker] = int(row["instrument_token"])
        except (TypeError, ValueError):
            continue

    qs = Symbol.objects.filter(exchange=Symbol.Exchange.NSE, is_active=True)
    if tickers:
        qs = qs.filter(ticker__in=tickers)

    updated = 0
    missing: list[str] = []
    for symbol in qs:
        token = token_by_ticker.get(symbol.ticker)
        if not token:
            missing.append(symbol.ticker)
            continue
        if symbol.instrument_token != token:
            symbol.instrument_token = token
            symbol.save(update_fields=["instrument_token"])
            updated += 1

    return {
        "status": "success",
        "updated": updated,
        "missing": missing,
        "total_symbols": qs.count(),
    }
