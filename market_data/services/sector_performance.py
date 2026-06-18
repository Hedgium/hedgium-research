"""Sector performance derived from constituent OHLCV."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from market_data.models import OHLCVDaily, SectorPerformance
from symbols.models import Sector, Symbol

logger = logging.getLogger(__name__)


def _pct_change(current: Decimal, previous: Decimal) -> Decimal | None:
    if previous is None or previous == 0:
        return None
    return ((current / previous) - 1) * 100


def _close_on_or_before(symbol_id: int, target: date) -> Decimal | None:
    row = (
        OHLCVDaily.objects.filter(symbol_id=symbol_id, date__lte=target)
        .order_by("-date")
        .values_list("close", flat=True)
        .first()
    )
    return row


def compute_sector_performance(as_of_date: date | None = None) -> dict:
    """
    Equal-weighted sector returns from NSE symbols grouped by company sector.
    """
    as_of_date = as_of_date or timezone.localdate()
    d1 = as_of_date - timedelta(days=1)
    d5 = as_of_date - timedelta(days=5)
    d20 = as_of_date - timedelta(days=20)

    symbols = (
        Symbol.objects.filter(is_active=True, exchange=Symbol.Exchange.NSE)
        .select_related("company", "company__sector")
        .exclude(company__sector__isnull=True)
    )

    sector_returns: dict[int, list[Decimal]] = defaultdict(list)
    sector_returns_5d: dict[int, list[Decimal]] = defaultdict(list)
    sector_returns_20d: dict[int, list[Decimal]] = defaultdict(list)

    for symbol in symbols:
        sector_id = symbol.company.sector_id
        close_today = _close_on_or_before(symbol.id, as_of_date)
        close_d1 = _close_on_or_before(symbol.id, d1)
        close_d5 = _close_on_or_before(symbol.id, d5)
        close_d20 = _close_on_or_before(symbol.id, d20)

        r1 = _pct_change(close_today, close_d1) if close_today and close_d1 else None
        r5 = _pct_change(close_today, close_d5) if close_today and close_d5 else None
        r20 = _pct_change(close_today, close_d20) if close_today and close_d20 else None

        if r1 is not None:
            sector_returns[sector_id].append(r1)
        if r5 is not None:
            sector_returns_5d[sector_id].append(r5)
        if r20 is not None:
            sector_returns_20d[sector_id].append(r20)

    updated = 0
    for sector in Sector.objects.all():
        r1_list = sector_returns.get(sector.id, [])
        if not r1_list:
            continue

        avg_1d = sum(r1_list) / len(r1_list)
        r5_list = sector_returns_5d.get(sector.id, [])
        r20_list = sector_returns_20d.get(sector.id, [])
        avg_5d = sum(r5_list) / len(r5_list) if r5_list else None
        avg_20d = sum(r20_list) / len(r20_list) if r20_list else None

        SectorPerformance.objects.update_or_create(
            sector=sector,
            date=as_of_date,
            defaults={
                "return_1d": avg_1d.quantize(Decimal("0.0001")),
                "return_5d": avg_5d.quantize(Decimal("0.0001")) if avg_5d is not None else None,
                "return_20d": avg_20d.quantize(Decimal("0.0001")) if avg_20d is not None else None,
            },
        )
        updated += 1

    return {
        "status": "success",
        "date": str(as_of_date),
        "sectors_updated": updated,
    }
