"""ML constants for 30-day direction classifier."""

from pathlib import Path

from django.conf import settings

FORWARD_DAYS = getattr(settings, "ML_FORWARD_DAYS", 30)
BULLISH_THRESHOLD = getattr(settings, "ML_BULLISH_THRESHOLD", 0.03)
BEARISH_THRESHOLD = getattr(settings, "ML_BEARISH_THRESHOLD", -0.03)

CLASS_BULLISH = 0
CLASS_BEARISH = 1
CLASS_SIDEWAYS = 2

CLASS_LABELS = {
    CLASS_BULLISH: "bullish",
    CLASS_BEARISH: "bearish",
    CLASS_SIDEWAYS: "sideways",
}

MODEL_TYPES = ("xgboost", "lightgbm", "catboost")
DEFAULT_VERSIONS = {
    "xgboost": "xgboost-v1",
    "lightgbm": "lightgbm-v1",
    "catboost": "catboost-v1",
}
DEFAULT_MODEL_VERSION = DEFAULT_VERSIONS["xgboost"]

FEATURE_COLUMNS = [
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_histogram",
    "macd_bullish_cross",
    "ema_20",
    "ema_50",
    "ema_200",
    "price_above_ema_20",
    "price_above_ema_50",
    "price_above_ema_200",
    "adx_14",
    "atr_14",
    "volume_spike",
    "vwap_proxy",
    "historical_volatility_20d",
    "beta_252",
    "sector_volatility_20d",
    "gap_count_60d",
    "gap_frequency_60d",
    "pe",
    "pb",
    "roe",
    "roce",
    "debt_equity",
    "profit_growth_yoy",
    "revenue_growth_yoy",
    "fundamental_data_available",
    "corp_active_event_count",
    "corp_ceo_resigned",
    "corp_cfo_resigned",
    "corp_sebi_action",
    "corp_promoter_selling",
    "fii_net",
    "dii_net",
    "sector_return_20d",
    "delivery_pct",
]


def get_model_dir() -> Path:
    base = getattr(settings, "ML_MODEL_DIR", None)
    if base:
        return Path(base)
    return Path(settings.BASE_DIR) / "analysis" / "ml" / "artifacts"


def artifact_path(version: str) -> Path:
    return get_model_dir() / version
