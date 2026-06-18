import logging

from celery import shared_task

from market_data.services.corporate_events import ingest_corporate_actions
from market_data.services.fii_dii import ingest_fii_dii
from market_data.services.ingestion import run_daily_ingestion
from market_data.services.ohlcv import ingest_ohlcv_universe
from market_data.services.sector_performance import compute_sector_performance

logger = logging.getLogger(__name__)


@shared_task(name="jobs.tasks.ingestion_tasks.ingest_ohlcv_daily")
def ingest_ohlcv_daily():
    logger.info("Ingesting OHLCV data")
    return run_daily_ingestion(ohlcv_days=5)


@shared_task(name="jobs.tasks.ingestion_tasks.ingest_ohlcv_kite_only")
def ingest_ohlcv_kite_only():
    logger.info("Ingesting OHLCV data from Kite")
    return ingest_ohlcv_universe(days=5, sync_tokens=True)


@shared_task(name="jobs.tasks.ingestion_tasks.ingest_fii_dii_daily")
def ingest_fii_dii_daily():
    logger.info("Ingesting FII and DII data")
    return ingest_fii_dii()


@shared_task(name="jobs.tasks.ingestion_tasks.compute_sector_performance_daily")
def compute_sector_performance_daily():
    logger.info("Computing sector performance")
    return compute_sector_performance()


@shared_task(name="jobs.tasks.ingestion_tasks.ingest_corporate_events")
def ingest_corporate_events_task():
    logger.info("Ingesting corporate events")
    return ingest_corporate_actions()
