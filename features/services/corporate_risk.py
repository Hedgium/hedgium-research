"""Corporate governance risk feature flags — derived from events."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from market_data.models import CorporateEvent

LOOKBACK_DAYS = 180

EVENT_FLAG_MAP = {
    CorporateEvent.EventType.CEO_RESIGN: "ceo_resigned",
    CorporateEvent.EventType.CFO_RESIGN: "cfo_resigned",
    CorporateEvent.EventType.AUDITOR_RESIGN: "auditor_resigned",
    CorporateEvent.EventType.SEBI_ACTION: "sebi_action",
    CorporateEvent.EventType.PROMOTER_SELL: "promoter_selling",
    CorporateEvent.EventType.PROMOTER_PLEDGE: "promoter_pledge_increased",
    CorporateEvent.EventType.MERGER: "merger",
    CorporateEvent.EventType.DEMERGER: "demerger",
}


def compute_corporate_risk_features(symbol) -> dict:
    cutoff = timezone.localdate() - timedelta(days=LOOKBACK_DAYS)
    events = CorporateEvent.objects.filter(symbol=symbol, event_date__gte=cutoff)

    flags = {flag: False for flag in EVENT_FLAG_MAP.values()}
    active_warnings: list[str] = []

    for event in events:
        flag_key = EVENT_FLAG_MAP.get(event.event_type)
        if flag_key:
            flags[flag_key] = True
            active_warnings.append(event.title)

    flags["active_event_count"] = events.count()
    flags["active_warnings"] = active_warnings[:10]
    flags["highest_severity"] = _highest_severity(events)
    return flags


def _highest_severity(events) -> str:
    order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    best = "LOW"
    for event in events:
        sev = event.severity or "MEDIUM"
        if order.get(sev, 0) > order.get(best, 0):
            best = sev
    return best
