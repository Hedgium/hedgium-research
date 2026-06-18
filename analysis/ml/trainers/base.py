"""Shared training utilities for tabular classifiers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from django.utils import timezone
from sklearn.metrics import accuracy_score, classification_report

from analysis.ml.constants import CLASS_LABELS, FEATURE_COLUMNS, artifact_path
from analysis.models import PredictionModelArtifact


def chronological_split(
    vectors: list[list[float]],
    labels: list[int],
    dates: list,
    test_size: float = 0.2,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    X = np.array(vectors, dtype=np.float32)
    y = np.array(labels, dtype=np.int32)
    order = np.argsort(dates)
    X = X[order]
    y = y[order]
    split_idx = int(len(X) * (1 - test_size))
    return X[:split_idx], X[split_idx:], y[:split_idx], y[split_idx:]


def evaluate_classifier(y_test: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    accuracy = float(accuracy_score(y_test, y_pred)) if len(y_test) else 0.0
    report = classification_report(
        y_test,
        y_pred,
        labels=[0, 1, 2],
        target_names=[CLASS_LABELS[i] for i in (0, 1, 2)],
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": accuracy,
        "classification_report": report,
        "bullish_f1": report.get("bullish", {}).get("f1-score"),
        "bearish_f1": report.get("bearish", {}).get("f1-score"),
        "sideways_f1": report.get("sideways", {}).get("f1-score"),
    }


def save_artifact(
    *,
    model,
    version: str,
    model_type: str,
    metrics: dict[str, Any],
    rows_total: int,
    rows_train: int,
    rows_test: int,
    index_name: str,
    sample_step: int,
    activate: bool = True,
) -> Path:
    out_dir = artifact_path(version)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_file = out_dir / "model.joblib"
    meta_file = out_dir / "metadata.json"

    joblib.dump(model, model_file)

    metadata = {
        "version": version,
        "model_type": model_type,
        "trained_at": timezone.now().isoformat(),
        "feature_columns": FEATURE_COLUMNS,
        "class_labels": CLASS_LABELS,
        "rows_total": rows_total,
        "rows_train": rows_train,
        "rows_test": rows_test,
        **metrics,
        "index_name": index_name,
        "sample_step": sample_step,
    }
    meta_file.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")

    if activate:
        PredictionModelArtifact.objects.filter(model_type=model_type, is_active=True).update(is_active=False)

    PredictionModelArtifact.objects.update_or_create(
        version=version,
        defaults={
            "model_type": model_type,
            "is_active": activate,
            "metrics": metadata,
            "artifact_path": str(model_file),
            "feature_columns": FEATURE_COLUMNS,
        },
    )
    return model_file
