from django.db import models

from symbols.models import Symbol


class PredictionModelArtifact(models.Model):
    """Registry of trained model artifacts on disk."""

    class ModelType(models.TextChoices):
        XGBOOST = "xgboost", "XGBoost"
        LIGHTGBM = "lightgbm", "LightGBM"
        CATBOOST = "catboost", "CatBoost"

    version = models.CharField(max_length=50, unique=True)
    model_type = models.CharField(
        max_length=20,
        choices=ModelType.choices,
        default=ModelType.XGBOOST,
        db_index=True,
    )
    is_active = models.BooleanField(default=False, db_index=True)
    metrics = models.JSONField(default=dict)
    artifact_path = models.CharField(max_length=500)
    feature_columns = models.JSONField(default=list)
    trained_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-trained_at"]

    def __str__(self):
        active = " (active)" if self.is_active else ""
        return f"{self.version}{active}"


class ModelPrediction(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="predictions")
    as_of_date = models.DateField(db_index=True)
    bullish_prob = models.DecimalField(max_digits=6, decimal_places=4)
    bearish_prob = models.DecimalField(max_digits=6, decimal_places=4)
    sideways_prob = models.DecimalField(max_digits=6, decimal_places=4)
    confidence_score = models.DecimalField(max_digits=6, decimal_places=4)
    model_version = models.CharField(max_length=50, default="xgboost-v0")

    class Meta:
        unique_together = [("symbol", "as_of_date", "model_version")]
        ordering = ["-as_of_date"]

    def __str__(self):
        return f"{self.symbol.ticker} prediction {self.as_of_date}"


class RiskAssessment(models.Model):
    class RiskLevel(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="risk_assessments")
    as_of_date = models.DateField(db_index=True)
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.LOW)
    risk_score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    warnings = models.JSONField(default=list)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [("symbol", "as_of_date")]
        ordering = ["-as_of_date"]

    def __str__(self):
        return f"{self.symbol.ticker} risk {self.risk_level} {self.as_of_date}"


class AnalysisReport(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="reports")
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    report = models.JSONField(default=dict)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["symbol", "-generated_at"]),
        ]

    def __str__(self):
        return f"{self.symbol.ticker} report {self.generated_at:%Y-%m-%d %H:%M}"
