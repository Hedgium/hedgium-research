import logging

from celery import shared_task
from django.conf import settings

from analysis.ml.predict import predict_universe
from analysis.services.report_builder import build_research_report
from symbols.models import Symbol

logger = logging.getLogger(__name__)


@shared_task(name="jobs.tasks.agent_tasks.precompute_agent_reports_daily")
def precompute_agent_reports_daily():
    """
    Optional async job to warm agent summaries for active NIFTY50 symbols.
    Disabled by default to avoid unnecessary LLM spend.
    """
    if not settings.AGENT_PRECOMPUTE_ENABLED:
        return {"status": "skipped", "reason": "AGENT_PRECOMPUTE_ENABLED is false"}

    # Ensure latest predictions are available before report synthesis
    predict_universe(use_ensemble=True)

    symbols = list(
        Symbol.objects.filter(
            is_active=True,
            exchange=Symbol.Exchange.NSE,
            index_memberships__index_name="NIFTY50",
        )
        .select_related("company")
        .order_by("ticker")
    )

    built = 0
    errors = []
    for symbol in symbols:
        try:
            build_research_report(symbol)
            built += 1
        except Exception as exc:  # pragma: no cover - defensive in async task
            errors.append({"symbol": symbol.ticker, "error": str(exc)})
            logger.exception("Agent precompute failed for %s", symbol.ticker)

    return {
        "status": "success" if not errors else "partial",
        "built": built,
        "errors": errors,
    }
