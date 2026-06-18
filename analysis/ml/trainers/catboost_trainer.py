"""CatBoost trainer."""

from __future__ import annotations

import numpy as np
from catboost import CatBoostClassifier

from analysis.ml.trainers.base import evaluate_classifier, save_artifact


MODEL_TYPE = "catboost"


def build_classifier() -> CatBoostClassifier:
    return CatBoostClassifier(
        loss_function="MultiClass",
        depth=6,
        learning_rate=0.08,
        iterations=300,
        random_seed=42,
        verbose=False,
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
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    if hasattr(y_pred, "flatten"):
        y_pred = y_pred.flatten()
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
