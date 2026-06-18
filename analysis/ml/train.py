"""Train multiclass direction models (XGBoost, LightGBM, CatBoost)."""

from __future__ import annotations

import logging

from analysis.ml.dataset import build_training_dataset
from analysis.ml.trainers import ALL_MODEL_TYPES, DEFAULT_VERSIONS, TRAINERS
from analysis.ml.trainers.base import chronological_split

logger = logging.getLogger(__name__)


def train_prediction_model(
    *,
    model_type: str = "xgboost",
    version: str | None = None,
    index_name: str = "NIFTY50",
    sample_step: int = 5,
    test_size: float = 0.2,
) -> dict:
    if model_type not in TRAINERS:
        return {"status": "error", "message": f"Unknown model_type: {model_type}"}

    version = version or DEFAULT_VERSIONS[model_type]
    trainer = TRAINERS[model_type]

    vectors, labels, dates, _ = build_training_dataset(
        index_name=index_name,
        sample_step=sample_step,
    )
    if len(vectors) < 100:
        return {
            "status": "error",
            "message": f"Insufficient training rows ({len(vectors)}). Need OHLCV backfill + features.",
        }

    X_train, X_test, y_train, y_test = chronological_split(vectors, labels, dates, test_size)

    return trainer.train(
        X_train,
        y_train,
        X_test,
        y_test,
        version=version,
        index_name=index_name,
        sample_step=sample_step,
        rows_total=len(vectors),
    )


def train_all_models(
    *,
    index_name: str = "NIFTY50",
    sample_step: int = 5,
    test_size: float = 0.2,
    model_types: list[str] | None = None,
) -> dict:
    types = model_types or ALL_MODEL_TYPES
    results = {}
    errors = []

    for model_type in types:
        try:
            results[model_type] = train_prediction_model(
                model_type=model_type,
                version=DEFAULT_VERSIONS.get(model_type),
                index_name=index_name,
                sample_step=sample_step,
                test_size=test_size,
            )
            if results[model_type].get("status") != "success":
                errors.append(model_type)
        except Exception as exc:
            logger.exception("Training failed for %s", model_type)
            results[model_type] = {"status": "error", "error": str(exc)}
            errors.append(model_type)

    return {
        "status": "success" if not errors else "partial",
        "failed": errors,
        "results": results,
    }
