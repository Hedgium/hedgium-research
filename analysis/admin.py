from django.contrib import admin

from analysis.models import AnalysisReport, ModelPrediction, PredictionModelArtifact, RiskAssessment


@admin.register(PredictionModelArtifact)
class PredictionModelArtifactAdmin(admin.ModelAdmin):
    list_display = ("version", "model_type", "is_active", "trained_at")
    list_filter = ("is_active", "model_type")
    readonly_fields = ("trained_at", "metrics", "feature_columns")


@admin.register(ModelPrediction)
class ModelPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "symbol",
        "as_of_date",
        "bullish_prob",
        "bearish_prob",
        "sideways_prob",
        "confidence_score",
        "model_version",
    )
    list_filter = ("model_version", "as_of_date")
    search_fields = ("symbol__ticker",)


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ("symbol", "as_of_date", "risk_level", "risk_score")
    list_filter = ("risk_level",)
    search_fields = ("symbol__ticker",)
    readonly_fields = ("details",)


@admin.register(AnalysisReport)
class AnalysisReportAdmin(admin.ModelAdmin):
    list_display = ("symbol", "generated_at")
    search_fields = ("symbol__ticker",)
    readonly_fields = ("generated_at", "report")
