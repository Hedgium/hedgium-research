"""Corporate actions ingestion from NSE."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from django.utils import timezone

from market_data.models import CorporateEvent
from symbols.models import Symbol

from .nse_client import NSEClient

logger = logging.getLogger(__name__)

EVENT_TYPE_MAP = {
    "bonus": CorporateEvent.EventType.BONUS,
    "split": CorporateEvent.EventType.SPLIT,
    "rights": CorporateEvent.EventType.RIGHTS,
    "merger": CorporateEvent.EventType.MERGER,
    "demerger": CorporateEvent.EventType.DEMERGER,
    "acquisition": CorporateEvent.EventType.ACQUISITION,
}


def _map_event_type(purpose: str) -> str | None:
    text = (purpose or "").lower()
    for key, event_type in EVENT_TYPE_MAP.items():
        if key in text:
            return event_type
    return None


def _parse_nse_date(value: str) -> date | None:
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def ingest_corporate_actions(
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    index_name: str = "NIFTY50",
) -> dict:
    to_date = to_date or timezone.localdate()
    from_date = from_date or (to_date - timedelta(days=30))

    client = NSEClient()
    path = (
        "/api/corporates-corporateActions"
        f"?index=equities&from_date={from_date.strftime('%d-%m-%Y')}"
        f"&to_date={to_date.strftime('%d-%m-%Y')}"
    )

    try:
        payload = client.get_json(path)
    except Exception as exc:
        logger.exception("Corporate actions fetch failed")
        return {"status": "error", "error": str(exc)}

    rows = payload if isinstance(payload, list) else payload.get("data", [])
    tickers = set(
        Symbol.objects.filter(
            index_memberships__index_name=index_name,
            exchange=Symbol.Exchange.NSE,
        ).values_list("ticker", flat=True)
    )
    symbol_map = {
        s.ticker: s
        for s in Symbol.objects.filter(ticker__in=tickers, exchange=Symbol.Exchange.NSE)
    }

    created = 0
    skipped = 0
    for row in rows:
        ticker = (row.get("symbol") or "").strip()
        if ticker not in symbol_map:
            skipped += 1
            continue

        purpose = row.get("subject") or row.get("purpose") or "Corporate action"
        ex_date = _parse_nse_date(row.get("exDate") or row.get("ex_date") or "")
        if not ex_date:
            skipped += 1
            continue

        event_type = _map_event_type(purpose)
        if not event_type:
            skipped += 1
            continue
        symbol = symbol_map[ticker]

        _, was_created = CorporateEvent.objects.get_or_create(
            symbol=symbol,
            event_type=event_type,
            event_date=ex_date,
            title=purpose[:500],
            defaults={
                "details": row,
                "severity": CorporateEvent.Severity.MEDIUM,
                "source": "NSE",
            },
        )
        if was_created:
            created += 1

    return {
        "status": "success",
        "from_date": str(from_date),
        "to_date": str(to_date),
        "created": created,
        "skipped": skipped,
    }
