"""Daily ingestion orchestrator."""

from __future__ import annotations

import logging

from market_data.services.bhavcopy import ingest_bhavcopy
from market_data.services.corporate_events import ingest_corporate_actions
from market_data.services.fii_dii import ingest_fii_dii
from market_data.services.ohlcv import ingest_ohlcv_universe
from market_data.services.sector_performance import compute_sector_performance

logger = logging.getLogger(__name__)


def run_daily_ingestion(*, ohlcv_days: int = 5) -> dict:
    """
    Post-market pipeline:
    1. Kite OHLCV (incremental)
    2. NSE bhavcopy (delivery % + EOD validation)
    3. FII/DII
    4. Sector performance
    5. Corporate actions (last 30 days window)
    """
    results = {}

    try:
        results["ohlcv"] = ingest_ohlcv_universe(days=ohlcv_days, sync_tokens=True)
    except Exception as exc:
        logger.exception("OHLCV ingestion failed")
        results["ohlcv"] = {"status": "error", "error": str(exc)}

    try:
        results["bhavcopy"] = ingest_bhavcopy()
    except Exception as exc:
        logger.exception("Bhavcopy ingestion failed")
        results["bhavcopy"] = {"status": "error", "error": str(exc)}

    try:
        results["fii_dii"] = ingest_fii_dii()
    except Exception as exc:
        logger.exception("FII/DII ingestion failed")
        results["fii_dii"] = {"status": "error", "error": str(exc)}

    try:
        results["sector_performance"] = compute_sector_performance()
    except Exception as exc:
        logger.exception("Sector performance computation failed")
        results["sector_performance"] = {"status": "error", "error": str(exc)}

    try:
        results["corporate_actions"] = ingest_corporate_actions()
    except Exception as exc:
        logger.exception("Corporate actions ingestion failed")
        results["corporate_actions"] = {"status": "error", "error": str(exc)}

    try:
        from features.services.compute import compute_features_universe

        results["features"] = compute_features_universe()
    except Exception as exc:
        logger.exception("Feature computation failed")
        results["features"] = {"status": "error", "error": str(exc)}

    try:
        from analysis.ml.predict import predict_universe

        results["predictions"] = predict_universe()
    except Exception as exc:
        logger.exception("Prediction failed")
        results["predictions"] = {"status": "error", "error": str(exc)}

    failed = [k for k, v in results.items() if v.get("status") == "error"]
    return {
        "status": "success" if not failed else "partial",
        "failed_steps": failed,
        "results": results,
    }
