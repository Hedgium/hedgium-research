"""Trainer registry for gradient boosting classifiers."""

from __future__ import annotations

from analysis.ml.trainers import catboost_trainer, lightgbm_trainer, xgboost_trainer

TRAINERS = {
    "xgboost": xgboost_trainer,
    "lightgbm": lightgbm_trainer,
    "catboost": catboost_trainer,
}

DEFAULT_VERSIONS = {
    "xgboost": "xgboost-v1",
    "lightgbm": "lightgbm-v1",
    "catboost": "catboost-v1",
}

ALL_MODEL_TYPES = list(TRAINERS.keys())
