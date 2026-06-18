"""LightGBM trainer."""

from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

from analysis.ml.constants import FEATURE_COLUMNS
from analysis.ml.trainers.base import evaluate_classifier, save_artifact


MODEL_TYPE = "lightgbm"


def build_classifier() -> LGBMClassifier:
    return LGBMClassifier(
        objective="multiclass",
        num_class=3,
        max_depth=6,
        learning_rate=0.08,
        n_estimators=300,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )


def train(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    *,
    version: str,
    index_name: str,
    sample_step: int,
    rows_total: int,
) -> dict:
    model = build_classifier()
    X_train_df = pd.DataFrame(X_train, columns=FEATURE_COLUMNS)
    X_test_df = pd.DataFrame(X_test, columns=FEATURE_COLUMNS)
    model.fit(X_train_df, y_train)
    y_pred = model.predict(X_test_df)
    metrics = evaluate_classifier(y_test, y_pred)

    model_file = save_artifact(
        model=model,
        version=version,
        model_type=MODEL_TYPE,
        metrics=metrics,
        rows_total=rows_total,
        rows_train=len(X_train),
        rows_test=len(X_test),
        index_name=index_name,
        sample_step=sample_step,
    )

    return {
        "status": "success",
        "model_type": MODEL_TYPE,
        "version": version,
        "accuracy": metrics["accuracy"],
        "rows_total": rows_total,
        "artifact": str(model_file),
        "metrics": {
            "bullish_f1": metrics["bullish_f1"],
            "bearish_f1": metrics["bearish_f1"],
            "sideways_f1": metrics["sideways_f1"],
        },
    }
