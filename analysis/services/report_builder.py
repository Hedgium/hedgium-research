from analysis.ml.predict import holding_outlook_from_probs
from analysis.models import ModelPrediction
from analysis.agents.orchestrator import run_specialized_agents
from analysis.schemas import build_stub_report
from analysis.services.risk_engine import assess_risk
from features.models import FeatureSnapshot
from market_data.models import DeliveryDaily, FIIDIIActivity, OHLCVDaily, SectorPerformance
from symbols.models import Symbol


def _positive_factors(feature_map: dict) -> list[str]:
    factors: list[str] = []
    technical = feature_map.get("TECHNICAL") or {}
    volatility = feature_map.get("VOLATILITY") or {}
    fundamental = feature_map.get("FUNDAMENTAL") or {}

    if technical.get("macd_bullish_cross"):
        factors.append("MACD bullish crossover")
    if technical.get("price_above_ema_50"):
        factors.append("Price above 50-day EMA")
    rsi = technical.get("rsi_14")
    if rsi is not None and 45 <= rsi <= 65:
        factors.append("RSI in healthy momentum zone")
    if (technical.get("volume_spike") or 0) > 1.5:
        factors.append("Volume spike vs 20-day average")

    beta = volatility.get("beta_252")
    if beta is not None and beta < 1.0:
        factors.append("Lower beta vs NIFTY 50 basket")

    if fundamental.get("data_available"):
        if (fundamental.get("roe") or 0) > 15:
            factors.append("Strong ROE")
        if (fundamental.get("profit_growth_yoy") or 0) > 10:
            factors.append("Positive profit growth YoY")

    return factors[:5]


def build_research_report(symbol: Symbol) -> dict:
    """
    Assemble report from pre-computed layers.
    Falls back to stub values when data is not yet available.
    """
    base = build_stub_report(symbol.ticker, symbol.company.name)
    base["status"] = "partial"

    ohlcv_count = OHLCVDaily.objects.filter(symbol=symbol).count()
    latest_ohlcv = (
        OHLCVDaily.objects.filter(symbol=symbol).order_by("-date").values_list("date", "close").first()
    )
    latest_delivery = (
        DeliveryDaily.objects.filter(symbol=symbol).order_by("-date").values_list("delivery_pct", flat=True).first()
    )

    if latest_ohlcv:
        base["status"] = "market_data_available"
        base["market_data"] = {
            "ohlcv_bars": ohlcv_count,
            "latest_date": str(latest_ohlcv[0]),
            "latest_close": float(latest_ohlcv[1]),
            "latest_delivery_pct": float(latest_delivery) if latest_delivery is not None else None,
        }

    sector = symbol.company.sector
    if sector:
        sector_perf = SectorPerformance.objects.filter(sector=sector).order_by("-date").first()
        if sector_perf:
            base.setdefault("market_data", {})
            base["market_data"]["sector_return_20d"] = (
                float(sector_perf.return_20d) if sector_perf.return_20d is not None else None
            )

    latest_fii = FIIDIIActivity.objects.order_by("-date").first()
    if latest_fii:
        base.setdefault("market_data", {})
        base["market_data"]["fii_net"] = float(latest_fii.fii_net) if latest_fii.fii_net is not None else None
        base["market_data"]["dii_net"] = float(latest_fii.dii_net) if latest_fii.dii_net is not None else None

    latest_features = (
        FeatureSnapshot.objects.filter(symbol=symbol)
        .order_by("-as_of_date")
        .first()
    )
    feature_map = {}
    feature_as_of = None
    if latest_features:
        base["status"] = "features_available"
        as_of = latest_features.as_of_date
        feature_as_of = str(as_of)
        snapshots = FeatureSnapshot.objects.filter(symbol=symbol, as_of_date=as_of)
        feature_map = {row.feature_group: row.features for row in snapshots}
        base["features"] = {
            "as_of_date": str(as_of),
            "technical": feature_map.get(FeatureSnapshot.FeatureGroup.TECHNICAL),
            "volatility": feature_map.get(FeatureSnapshot.FeatureGroup.VOLATILITY),
            "fundamental": feature_map.get(FeatureSnapshot.FeatureGroup.FUNDAMENTAL),
            "corporate_risk": feature_map.get(FeatureSnapshot.FeatureGroup.CORPORATE_RISK),
        }
        base["key_positive_factors"] = _positive_factors(feature_map)

    risk = assess_risk(symbol)
    base["risk_level"] = risk["risk_level"]
    base["risk_score"] = risk.get("risk_score")
    base["risk_rules"] = risk.get("rules", [])
    base["risk_factors"] = risk["warnings"]

    prediction = (
        ModelPrediction.objects.filter(symbol=symbol, model_version="ensemble-v1")
        .order_by("-as_of_date", "-id")
        .first()
    ) or (
        ModelPrediction.objects.filter(symbol=symbol)
        .order_by("-as_of_date", "-id")
        .first()
    )
    if prediction:
        base["status"] = "prediction_available"
        base["probabilities"] = {
            "bullish": float(prediction.bullish_prob),
            "bearish": float(prediction.bearish_prob),
            "sideways": float(prediction.sideways_prob),
        }
        base["confidence_score"] = float(prediction.confidence_score)
        base["holding_outlook"] = holding_outlook_from_probs(base["probabilities"])
        base["model_version"] = prediction.model_version

    # Agent synthesis layer (Phase 4)
    if feature_map:
        predictions_payload = base.get("probabilities", {})
        agent_result = run_specialized_agents(
            symbol=symbol,
            company_name=symbol.company.name,
            as_of_date=feature_as_of or base["generated_at"].date().isoformat(),
            feature_map=feature_map,
            predictions=predictions_payload,
            risk=risk,
        )
        base["agent_insights"] = agent_result
        master = agent_result.get("master", {})
        if master:
            if master.get("key_positive_factors"):
                base["key_positive_factors"] = master["key_positive_factors"][:5]
            if master.get("risk_factors"):
                base["risk_factors"] = master["risk_factors"][:8]
            if master.get("holding_outlook"):
                base["holding_outlook"] = master["holding_outlook"]
            if master.get("news_summary"):
                base["news_summary"] = master["news_summary"]

    return base
