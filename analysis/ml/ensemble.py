"""Blend predictions from multiple active models."""

from __future__ import annotations

from analysis.ml.constants import CLASS_BEARISH, CLASS_BULLISH, CLASS_LABELS, CLASS_SIDEWAYS

ENSEMBLE_VERSION = "ensemble-v1"


def blend_probabilities(model_probs: list[dict]) -> dict | None:
    if not model_probs:
        return None

    bullish = sum(p["bullish"] for p in model_probs) / len(model_probs)
    bearish = sum(p["bearish"] for p in model_probs) / len(model_probs)
    sideways = sum(p["sideways"] for p in model_probs) / len(model_probs)

    # Renormalize in case of float drift
    total = bullish + bearish + sideways
    if total > 0:
        bullish /= total
        bearish /= total
        sideways /= total

    probs = [bullish, bearish, sideways]
    predicted_idx = max(range(3), key=lambda i: probs[i])

    return {
        "bullish": bullish,
        "bearish": bearish,
        "sideways": sideways,
        "confidence_score": max(probs),
        "predicted_class": CLASS_LABELS[predicted_idx],
        "models_used": len(model_probs),
    }
