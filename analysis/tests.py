from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from analysis.models import ModelPrediction, RiskAssessment
from analysis.services.report_builder import build_research_report
from analysis.services.risk_engine import assess_risk
from features.models import FeatureSnapshot
from market_data.models import CorporateEvent, NewsArticle, OHLCVDaily
from symbols.models import Company, Sector, Symbol


class RiskEngineTests(TestCase):
    def setUp(self):
        self.sector = Sector.objects.create(name="IT")
        self.company = Company.objects.create(name="Test Corp", sector=self.sector)
        self.symbol = Symbol.objects.create(
            company=self.company,
            ticker="TEST",
            exchange=Symbol.Exchange.NSE,
            is_active=True,
        )

    def test_risk_engine_returns_structured_rules_and_persists(self):
        CorporateEvent.objects.create(
            symbol=self.symbol,
            event_type=CorporateEvent.EventType.SEBI_ACTION,
            event_date=timezone.localdate(),
            title="SEBI inquiry reported",
            severity=CorporateEvent.Severity.CRITICAL,
            source="NSE",
        )
        result = assess_risk(self.symbol, persist=True)
        self.assertEqual(result["risk_level"], "CRITICAL")
        self.assertGreater(result["risk_score"], 0)
        self.assertTrue(result["rules"])

        assessment = RiskAssessment.objects.get(symbol=self.symbol, as_of_date=timezone.localdate())
        self.assertEqual(assessment.risk_level, "CRITICAL")
        self.assertGreater(assessment.risk_score, 0)
        self.assertIn("rules", assessment.details)


class ReportBuilderTests(TestCase):
    @override_settings(AGENT_ENABLE=False)
    def test_report_builder_returns_prediction_and_agent_insights(self):
        sector = Sector.objects.create(name="Banking")
        company = Company.objects.create(name="TCS Demo", sector=sector)
        symbol = Symbol.objects.create(
            company=company,
            ticker="TCSD",
            exchange=Symbol.Exchange.NSE,
            is_active=True,
        )

        OHLCVDaily.objects.create(
            symbol=symbol,
            date=timezone.localdate(),
            open=Decimal("100"),
            high=Decimal("110"),
            low=Decimal("95"),
            close=Decimal("108"),
            volume=100000,
        )
        FeatureSnapshot.objects.create(
            symbol=symbol,
            as_of_date=timezone.localdate(),
            feature_group=FeatureSnapshot.FeatureGroup.TECHNICAL,
            features={"macd_bullish_cross": True, "price_above_ema_50": True},
        )
        FeatureSnapshot.objects.create(
            symbol=symbol,
            as_of_date=timezone.localdate(),
            feature_group=FeatureSnapshot.FeatureGroup.VOLATILITY,
            features={"beta_252": 0.9},
        )
        FeatureSnapshot.objects.create(
            symbol=symbol,
            as_of_date=timezone.localdate(),
            feature_group=FeatureSnapshot.FeatureGroup.FUNDAMENTAL,
            features={"data_available": False},
        )
        FeatureSnapshot.objects.create(
            symbol=symbol,
            as_of_date=timezone.localdate(),
            feature_group=FeatureSnapshot.FeatureGroup.CORPORATE_RISK,
            features={"active_event_count": 0},
        )
        NewsArticle.objects.create(
            symbol=symbol,
            title="Company wins major contract",
            source="ET",
            published_at=timezone.now(),
            sentiment=NewsArticle.Sentiment.POSITIVE,
        )
        ModelPrediction.objects.create(
            symbol=symbol,
            as_of_date=timezone.localdate(),
            bullish_prob=Decimal("0.71"),
            bearish_prob=Decimal("0.18"),
            sideways_prob=Decimal("0.11"),
            confidence_score=Decimal("0.83"),
            model_version="ensemble-v1",
        )

        report = build_research_report(symbol)
        self.assertEqual(report["model_version"], "ensemble-v1")
        self.assertEqual(report["risk_level"], "LOW")
        self.assertIn("agent_insights", report)
        self.assertIn("technical", report["agent_insights"])
