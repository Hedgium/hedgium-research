from datetime import timedelta

from django.utils import timezone

from analysis.models import RiskAssessment
from market_data.models import CorporateEvent

RISK_LEVEL_ORDER = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}

EVENT_SEVERITY = {
    CorporateEvent.EventType.CEO_RESIGN: "HIGH",
    CorporateEvent.EventType.CFO_RESIGN: "HIGH",
    CorporateEvent.EventType.AUDITOR_RESIGN: "HIGH",
    CorporateEvent.EventType.SEBI_ACTION: "CRITICAL",
    CorporateEvent.EventType.PROMOTER_SELL: "MEDIUM",
    CorporateEvent.EventType.PROMOTER_PLEDGE: "HIGH",
    CorporateEvent.EventType.MERGER: "MEDIUM",
    CorporateEvent.EventType.DEMERGER: "MEDIUM",
}

SEVERITY_WEIGHT = {
    "LOW": 1.0,
    "MEDIUM": 2.0,
    "HIGH": 3.5,
    "CRITICAL": 5.0,
}

RISK_SCORE_LEVELS = [
    (0.0, "LOW"),
    (3.0, "MEDIUM"),
    (7.0, "HIGH"),
    (12.0, "CRITICAL"),
]


def _max_risk_level(levels: list[str]) -> str:
    if not levels:
        return "LOW"
    return max(levels, key=lambda level: RISK_LEVEL_ORDER.get(level, 0))


def _score_to_level(score: float) -> str:
    level = "LOW"
    for threshold, candidate in RISK_SCORE_LEVELS:
        if score >= threshold:
            level = candidate
    return level


def _build_rule(event: CorporateEvent) -> dict:
    severity = event.severity or EVENT_SEVERITY.get(event.event_type, "MEDIUM")
    return {
        "code": event.event_type,
        "severity": severity,
        "weight": SEVERITY_WEIGHT.get(severity, 2.0),
        "evidence": {
            "title": event.title,
            "event_date": str(event.event_date),
        },
        "source": event.source or "corporate_event",
    }


def assess_risk(symbol, *, persist: bool = True) -> dict:
    """Deterministic rule-based risk engine with structured evidence."""
    cutoff = timezone.now().date() - timedelta(days=180)
    events = CorporateEvent.objects.filter(
        symbol=symbol,
        event_date__gte=cutoff,
    ).order_by("-event_date")

    warnings: list[str] = []
    severities: list[str] = []
    rules: list[dict] = []

    for event in events:
        severity = event.severity or EVENT_SEVERITY.get(event.event_type, "MEDIUM")
        severities.append(severity)
        warnings.append(event.title)
        rules.append(_build_rule(event))

    score = round(sum(rule["weight"] for rule in rules), 2)
    level_from_score = _score_to_level(score)
    level_from_severity = _max_risk_level(severities)
    risk_level = level_from_score if RISK_LEVEL_ORDER[level_from_score] >= RISK_LEVEL_ORDER[level_from_severity] else level_from_severity

    result = {
        "risk_level": risk_level,
        "risk_score": score,
        "warnings": warnings[:10],
        "rules": rules,
    }

    if persist:
        RiskAssessment.objects.update_or_create(
            symbol=symbol,
            as_of_date=timezone.localdate(),
            defaults={
                "risk_level": risk_level,
                "risk_score": score,
                "warnings": warnings[:10],
                "details": {"rules": rules},
            },
        )

    return result
