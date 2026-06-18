"""Serve ML predictions — XGBoost, LightGBM, CatBoost + ensemble."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

import joblib
import pandas as pd

from analysis.ml.constants import CLASS_BEARISH, CLASS_BULLISH, CLASS_LABELS, CLASS_SIDEWAYS, FEATURE_COLUMNS
from analysis.ml.ensemble import ENSEMBLE_VERSION, blend_probabilities
from analysis.ml.feature_vector import build_feature_row, row_to_vector
from analysis.models import ModelPrediction, PredictionModelArtifact
from features.models import FeatureSnapshot
from market_data.models import DeliveryDaily, FIIDIIActivity, SectorPerformance
from symbols.models import Symbol
import numpy as np

logger = logging.getLogger(__name__)


def get_active_models() -> list[tuple[object, PredictionModelArtifact]]:
    artifacts = PredictionModelArtifact.objects.filter(is_active=True).order_by("model_type")
    loaded = []
    for artifact in artifacts:
        path = Path(artifact.artifact_path)
        if not path.exists():
            logger.error("Model artifact missing: %s", path)
            continue
        loaded.append((joblib.load(path), artifact))
    return loaded


def get_active_model():
    """Backward-compatible: return first active model."""
    models = get_active_models()
    if not models:
        return None, None
    model, artifact = models[0]
    return model, artifact


def _market_context_for_symbol(symbol: Symbol) -> dict:
    ctx: dict = {}
    latest_fii = FIIDIIActivity.objects.order_by("-date").first()
    if latest_fii:
        ctx["fii_net"] = float(latest_fii.fii_net) if latest_fii.fii_net is not None else None
        ctx["dii_net"] = float(latest_fii.dii_net) if latest_fii.dii_net is not None else None

    sector = symbol.company.sector
    if sector:
        perf = SectorPerformance.objects.filter(sector=sector).order_by("-date").first()
        if perf and perf.return_20d is not None:
            ctx["sector_return_20d"] = float(perf.return_20d)

    delivery = (
        DeliveryDaily.objects.filter(symbol=symbol).order_by("-date").values_list("delivery_pct", flat=True).first()
    )
    if delivery is not None:
        ctx["delivery_pct"] = float(delivery)
    return ctx


def feature_vector_from_snapshots(symbol: Symbol, as_of_date: date | None = None) -> tuple[dict, date] | None:
    qs = FeatureSnapshot.objects.filter(symbol=symbol)
    if as_of_date:
        qs = qs.filter(as_of_date=as_of_date)
    latest = qs.order_by("-as_of_date").first()
    if not latest:
        return None

    as_of = latest.as_of_date
    snapshots = FeatureSnapshot.objects.filter(symbol=symbol, as_of_date=as_of)
    groups = {row.feature_group: row.features for row in snapshots}

    row = build_feature_row(
        technical=groups.get(FeatureSnapshot.FeatureGroup.TECHNICAL),
        volatility=groups.get(FeatureSnapshot.FeatureGroup.VOLATILITY),
        fundamental=groups.get(FeatureSnapshot.FeatureGroup.FUNDAMENTAL),
        corporate_risk=groups.get(FeatureSnapshot.FeatureGroup.CORPORATE_RISK),
        market_context=_market_context_for_symbol(symbol),
    )
    return row, as_of


def _proba_from_model(model, vector: list[float]) -> dict:
    X = pd.DataFrame([vector], columns=FEATURE_COLUMNS)
    probs = model.predict_proba(X)[0]
    bullish = float(probs[CLASS_BULLISH])
    bearish = float(probs[CLASS_BEARISH])
    sideways = float(probs[CLASS_SIDEWAYS])
    return {
        "bullish": bullish,
        "bearish": bearish,
        "sideways": sideways,
        "confidence_score": float(max(probs)),
        "predicted_class": CLASS_LABELS[int(np.argmax(probs))],
    }


def predict_proba(vector: list[float], model=None) -> dict | None:
    if model is None:
        model, _ = get_active_model()
    if model is None:
        return None
    return _proba_from_model(model, vector)


def _persist_prediction(symbol: Symbol, as_of_date: date, model_version: str, probs: dict) -> None:
    ModelPrediction.objects.update_or_create(
        symbol=symbol,
        as_of_date=as_of_date,
        model_version=model_version,
        defaults={
            "bullish_prob": Decimal(str(round(probs["bullish"], 4))),
            "bearish_prob": Decimal(str(round(probs["bearish"], 4))),
            "sideways_prob": Decimal(str(round(probs["sideways"], 4))),
            "confidence_score": Decimal(str(round(probs["confidence_score"], 4))),
        },
    )


def holding_outlook_from_probs(probs: dict) -> dict:
    bullish = probs["bullish"]
    bearish = probs["bearish"]
    sideways = probs["sideways"]

    if bullish >= bearish and bullish >= sideways:
        if bullish >= 0.7:
            stance = "Bullish"
        elif bullish >= 0.5:
            stance = "Moderately Bullish"
        else:
            stance = "Slightly Bullish"
    elif bearish >= bullish and bearish >= sideways:
        if bearish >= 0.7:
            stance = "Bearish"
        elif bearish >= 0.5:
            stance = "Moderately Bearish"
        else:
            stance = "Slightly Bearish"
    else:
        stance = "Neutral / Sideways"

    return {"horizon_days": "30-60", "stance": stance}


def predict_symbol(symbol: Symbol, *, persist: bool = True, use_ensemble: bool = True) -> dict:
    built = feature_vector_from_snapshots(symbol)
    if not built:
        return {"symbol": symbol.ticker, "status": "skipped", "reason": "no feature snapshots"}

    feature_row, as_of_date = built
    vector = row_to_vector(feature_row)
    active_models = get_active_models()

    if not active_models:
        return {"symbol": symbol.ticker, "status": "skipped", "reason": "no trained model"}

    per_model: dict[str, dict] = {}
    model_probs: list[dict] = []

    for model, artifact in active_models:
        probs = _proba_from_model(model, vector)
        per_model[artifact.model_type] = {
            "version": artifact.version,
            **probs,
        }
        model_probs.append(probs)
        if persist:
            _persist_prediction(symbol, as_of_date, artifact.version, probs)

    if use_ensemble and len(model_probs) > 1:
        ensemble_probs = blend_probabilities(model_probs)
    elif model_probs:
        ensemble_probs = model_probs[0]
    else:
        return {"symbol": symbol.ticker, "status": "error", "reason": "prediction failed"}

    if persist and use_ensemble:
        _persist_prediction(symbol, as_of_date, ENSEMBLE_VERSION, ensemble_probs)

    result = {
        "symbol": symbol.ticker,
        "status": "success",
        "as_of_date": str(as_of_date),
        "model_version": ENSEMBLE_VERSION if use_ensemble and len(model_probs) > 1 else active_models[0][1].version,
        **ensemble_probs,
        "holding_outlook": holding_outlook_from_probs(ensemble_probs),
        "per_model": per_model,
    }
    return result


def predict_universe(
    *,
    index_name: str = "NIFTY50",
    tickers: list[str] | None = None,
    use_ensemble: bool = True,
) -> dict:
    qs = Symbol.objects.filter(
        is_active=True,
        exchange=Symbol.Exchange.NSE,
        index_memberships__index_name=index_name,
    ).distinct()
    if tickers:
        qs = qs.filter(ticker__in=tickers)

    results = []
    skipped = 0
    errors = []

    for symbol in qs.order_by("ticker"):
        try:
            row = predict_symbol(symbol, use_ensemble=use_ensemble)
            results.append(row)
            if row.get("status") == "skipped":
                skipped += 1
        except Exception as exc:
            logger.exception("Prediction failed for %s", symbol.ticker)
            errors.append({"symbol": symbol.ticker, "error": str(exc)})

    return {
        "status": "success" if not errors else "partial",
        "predictions": len(results),
        "skipped": skipped,
        "errors": errors,
        "results": results,
    }
