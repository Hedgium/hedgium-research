from datetime import datetime

from django.shortcuts import get_object_or_404
from ninja import Router

from analysis.models import AnalysisReport
from analysis.schemas import HealthOut, ResearchReportOut, build_stub_report
from analysis.services.report_builder import build_research_report
from symbols.models import Symbol

router = Router()


@router.get("health/", response=HealthOut)
def health(request):
    return {
        "status": "ok",
        "service": "hedgium_research",
        "timestamp": datetime.now(),
    }


@router.get("{symbol}/", response=ResearchReportOut)
def get_research_report(request, symbol: str):
    symbol_obj = get_object_or_404(
        Symbol.objects.select_related("company"),
        ticker__iexact=symbol.strip(),
        exchange=Symbol.Exchange.NSE,
        is_active=True,
    )
    report_data = build_research_report(symbol_obj)
    db_payload = {
        **report_data,
        "generated_at": report_data["generated_at"].isoformat(),
    }
    AnalysisReport.objects.create(symbol=symbol_obj, report=db_payload)
    return report_data


@router.get("{symbol}/latest/", response=ResearchReportOut)
def get_latest_cached_report(request, symbol: str):
    symbol_obj = get_object_or_404(
        Symbol.objects.select_related("company"),
        ticker__iexact=symbol.strip(),
        exchange=Symbol.Exchange.NSE,
        is_active=True,
    )
    latest = (
        AnalysisReport.objects.filter(symbol=symbol_obj)
        .order_by("-generated_at")
        .first()
    )
    if latest:
        return latest.report
    return build_research_report(symbol_obj)
