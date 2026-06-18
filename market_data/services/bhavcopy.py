"""NSE bhavcopy ingestion — OHLCV validation + delivery %."""

from __future__ import annotations

import csv
import io
import logging
import zipfile
from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone

from market_data.models import DeliveryDaily, OHLCVDaily
from symbols.models import Symbol

from .nse_client import NSE_ARCHIVES, NSEClient

logger = logging.getLogger(__name__)


def _parse_decimal(value: str) -> Decimal:
    value = (value or "").strip().replace(",", "")
    if not value or value == "-":
        return Decimal("0")
    return Decimal(value)


def _parse_int(value: str) -> int:
    value = (value or "").strip().replace(",", "")
    if not value or value == "-":
        return 0
    return int(float(value))


def parse_bhavcopy_csv(csv_text: str) -> list[dict]:
    """Parse NSE cm*bhav.csv content into normalized rows."""
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = []
    for raw in reader:
        ticker = (raw.get("SYMBOL") or raw.get("Symbol") or "").strip()
        if not ticker:
            continue
        series = (raw.get("SERIES") or raw.get("Series") or "").strip()
        if series and series != "EQ":
            continue

        try:
            trade_date = datetime.strptime(
                (raw.get("TIMESTAMP") or raw.get("Date") or "").strip(),
                "%d-%b-%Y",
            ).date()
        except ValueError:
            continue

        traded_qty = _parse_int(raw.get("TOTTRDQTY") or raw.get("TTL_TRD_QNTY") or "0")
        delivery_qty = _parse_int(raw.get("DELIV_QTY") or raw.get("DELIVRY_QTY") or "0")
        delivery_pct = Decimal("0")
        if traded_qty > 0:
            delivery_pct = (Decimal(delivery_qty) / Decimal(traded_qty) * 100).quantize(
                Decimal("0.0001")
            )

        rows.append(
            {
                "ticker": ticker,
                "date": trade_date,
                "open": _parse_decimal(raw.get("OPEN") or raw.get("OPEN_PRICE") or "0"),
                "high": _parse_decimal(raw.get("HIGH") or raw.get("HIGH_PRICE") or "0"),
                "low": _parse_decimal(raw.get("LOW") or raw.get("LOW_PRICE") or "0"),
                "close": _parse_decimal(raw.get("CLOSE") or raw.get("CLOSE_PRICE") or "0"),
                "volume": traded_qty,
                "delivery_qty": delivery_qty,
                "delivery_pct": delivery_pct,
            }
        )
    return rows


def _bhavcopy_urls(trade_date: date) -> list[str]:
    year = trade_date.strftime("%Y")
    month = trade_date.strftime("%b").upper()
    stamp = trade_date.strftime("%d%b%Y").upper()
    ddmmyyyy = trade_date.strftime("%d%m%Y")
    return [
        (
            f"{NSE_ARCHIVES}/content/historical/EQUITIES/{year}/{month}/"
            f"cm{stamp}bhav.csv.zip"
        ),
        f"{NSE_ARCHIVES}/products/content/sec_bhavdata_full_{ddmmyyyy}.csv",
    ]


def fetch_bhavcopy(trade_date: date, client: NSEClient | None = None) -> str:
    client = client or NSEClient()
    errors: list[str] = []
    for url in _bhavcopy_urls(trade_date):
        try:
            content = client.get_bytes(url)
            if url.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    csv_name = next(
                        name for name in zf.namelist() if name.lower().endswith(".csv")
                    )
                    return zf.read(csv_name).decode("utf-8", errors="replace")
            return content.decode("utf-8", errors="replace")
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError("; ".join(errors))


def ingest_bhavcopy(
    trade_date: date | None = None,
    *,
    tickers: list[str] | None = None,
) -> dict:
    """Ingest OHLCV + delivery from NSE bhavcopy for one trade date."""
    trade_date = trade_date or timezone.localdate()
    client = NSEClient()

    try:
        csv_text = fetch_bhavcopy(trade_date, client=client)
    except Exception as exc:
        logger.exception("Bhavcopy fetch failed for %s", trade_date)
        return {"status": "error", "date": str(trade_date), "error": str(exc)}

    parsed = parse_bhavcopy_csv(csv_text)
    if tickers:
        ticker_set = {t.upper() for t in tickers}
        parsed = [row for row in parsed if row["ticker"] in ticker_set]

    symbol_map = {
        s.ticker: s
        for s in Symbol.objects.filter(
            exchange=Symbol.Exchange.NSE,
            is_active=True,
            ticker__in=[row["ticker"] for row in parsed],
        )
    }

    ohlcv_rows = []
    delivery_rows = []
    skipped = 0

    for row in parsed:
        symbol = symbol_map.get(row["ticker"])
        if not symbol:
            skipped += 1
            continue
        ohlcv_rows.append(
            OHLCVDaily(
                symbol=symbol,
                date=row["date"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
            )
        )
        delivery_rows.append(
            DeliveryDaily(
                symbol=symbol,
                date=row["date"],
                traded_qty=row["volume"],
                delivery_qty=row["delivery_qty"],
                delivery_pct=row["delivery_pct"],
            )
        )

    if ohlcv_rows:
        OHLCVDaily.objects.bulk_create(
            ohlcv_rows,
            update_conflicts=True,
            update_fields=["open", "high", "low", "close", "volume"],
            unique_fields=["symbol", "date"],
        )
    if delivery_rows:
        DeliveryDaily.objects.bulk_create(
            delivery_rows,
            update_conflicts=True,
            update_fields=["traded_qty", "delivery_qty", "delivery_pct"],
            unique_fields=["symbol", "date"],
        )

    return {
        "status": "success",
        "date": str(trade_date),
        "ohlcv_rows": len(ohlcv_rows),
        "delivery_rows": len(delivery_rows),
        "skipped_unknown": skipped,
    }
