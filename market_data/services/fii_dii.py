"""FII/DII daily flow ingestion from NSE."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from market_data.models import FIIDIIActivity

from .nse_client import NSEClient

logger = logging.getLogger(__name__)


def _to_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        cleaned = str(value).replace(",", "").strip()
        if not cleaned or cleaned == "-":
            return None
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def ingest_fii_dii(trade_date: date | None = None) -> dict:
    """
    Fetch FII/DII provisional data from NSE JSON API.
    Stores market-level net flows for the trade date.
    """
    trade_date = trade_date or timezone.localdate()
    client = NSEClient()

    try:
        payload = client.get_json("/api/fiidiiTradeReact")
    except Exception as exc:
        logger.exception("FII/DII fetch failed")
        return {"status": "error", "date": str(trade_date), "error": str(exc)}

    if not isinstance(payload, list) or not payload:
        return {"status": "error", "date": str(trade_date), "error": "empty FII/DII payload"}

    # NSE returns category rows — pick FII and DII net values
    fii_net = None
    dii_net = None
    fii_buy = fii_sell = dii_buy = dii_sell = None

    for row in payload:
        category = (row.get("category") or "").strip().upper()
        if category == "FII/FPI":
            fii_buy = _to_decimal(row.get("buyValue"))
            fii_sell = _to_decimal(row.get("sellValue"))
            fii_net = _to_decimal(row.get("netValue"))
        elif category == "DII":
            dii_buy = _to_decimal(row.get("buyValue"))
            dii_sell = _to_decimal(row.get("sellValue"))
            dii_net = _to_decimal(row.get("netValue"))

    if fii_net is None and dii_net is None:
        return {"status": "error", "date": str(trade_date), "error": "FII/DII values not found"}

    obj, created = FIIDIIActivity.objects.update_or_create(
        date=trade_date,
        defaults={
            "fii_buy": fii_buy,
            "fii_sell": fii_sell,
            "fii_net": fii_net,
            "dii_buy": dii_buy,
            "dii_sell": dii_sell,
            "dii_net": dii_net,
        },
    )

    return {
        "status": "success",
        "date": str(trade_date),
        "created": created,
        "fii_net": float(fii_net) if fii_net is not None else None,
        "dii_net": float(dii_net) if dii_net is not None else None,
        "id": obj.id,
    }
