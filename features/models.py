from django.db import models

from symbols.models import Symbol


class FundamentalMetric(models.Model):
    """Quarterly fundamentals — import via CSV or future vendor API."""

    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="fundamentals")
    period_end = models.DateField(db_index=True)
    pe = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    pb = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    roe = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    roce = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    debt_equity = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    profit_growth_yoy = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    revenue_growth_yoy = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    source = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        unique_together = [("symbol", "period_end")]
        ordering = ["-period_end"]

    def __str__(self):
        return f"{self.symbol.ticker} fundamentals {self.period_end}"


class FeatureSnapshot(models.Model):
    class FeatureGroup(models.TextChoices):
        TECHNICAL = "TECHNICAL", "Technical"
        VOLATILITY = "VOLATILITY", "Volatility"
        FUNDAMENTAL = "FUNDAMENTAL", "Fundamental"
        CORPORATE_RISK = "CORPORATE_RISK", "Corporate risk"

    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="feature_snapshots")
    as_of_date = models.DateField(db_index=True)
    feature_group = models.CharField(max_length=20, choices=FeatureGroup.choices, db_index=True)
    features = models.JSONField(default=dict)

    class Meta:
        unique_together = [("symbol", "as_of_date", "feature_group")]
        ordering = ["-as_of_date"]
        indexes = [
            models.Index(fields=["symbol", "as_of_date"]),
        ]

    def __str__(self):
        return f"{self.symbol.ticker} {self.feature_group} {self.as_of_date}"
