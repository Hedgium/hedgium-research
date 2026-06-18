from django.db import models

from symbols.models import Sector, Symbol


class OHLCVDaily(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="ohlcv")
    date = models.DateField(db_index=True)
    open = models.DecimalField(max_digits=14, decimal_places=4)
    high = models.DecimalField(max_digits=14, decimal_places=4)
    low = models.DecimalField(max_digits=14, decimal_places=4)
    close = models.DecimalField(max_digits=14, decimal_places=4)
    volume = models.BigIntegerField(default=0)

    class Meta:
        verbose_name = "OHLCV daily"
        verbose_name_plural = "OHLCV daily"
        unique_together = [("symbol", "date")]
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["symbol", "date"]),
        ]

    def __str__(self):
        return f"{self.symbol.ticker} {self.date}"


class DeliveryDaily(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="delivery")
    date = models.DateField(db_index=True)
    traded_qty = models.BigIntegerField(default=0)
    delivery_qty = models.BigIntegerField(default=0)
    delivery_pct = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    class Meta:
        verbose_name = "Delivery daily"
        verbose_name_plural = "Delivery daily"
        unique_together = [("symbol", "date")]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.symbol.ticker} delivery {self.date}"


class FIIDIIActivity(models.Model):
    date = models.DateField(unique=True, db_index=True)
    fii_buy = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    fii_sell = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    fii_net = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    dii_buy = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    dii_sell = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    dii_net = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "FII/DII activity"
        verbose_name_plural = "FII/DII activity"
        ordering = ["-date"]

    def __str__(self):
        return f"FII/DII {self.date}"


class SectorPerformance(models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="performance")
    date = models.DateField(db_index=True)
    return_1d = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    return_5d = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    return_20d = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    class Meta:
        unique_together = [("sector", "date")]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.sector.name} {self.date}"


class CorporateEvent(models.Model):
    class EventType(models.TextChoices):
        BONUS = "BONUS", "Bonus"
        SPLIT = "SPLIT", "Split"
        RIGHTS = "RIGHTS", "Rights issue"
        MERGER = "MERGER", "Merger"
        DEMERGER = "DEMERGER", "Demerger"
        ACQUISITION = "ACQUISITION", "Acquisition"
        PROMOTER_STAKE = "PROMOTER_STAKE", "Promoter stake change"
        CEO_RESIGN = "CEO_RESIGN", "CEO resigned"
        CFO_RESIGN = "CFO_RESIGN", "CFO resigned"
        AUDITOR_RESIGN = "AUDITOR_RESIGN", "Auditor resigned"
        SEBI_ACTION = "SEBI_ACTION", "SEBI action"
        PROMOTER_SELL = "PROMOTER_SELL", "Promoter selling"
        PROMOTER_PLEDGE = "PROMOTER_PLEDGE", "Promoter pledge change"

    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    symbol = models.ForeignKey(
        Symbol,
        on_delete=models.CASCADE,
        related_name="corporate_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    event_date = models.DateField(db_index=True)
    title = models.CharField(max_length=500)
    details = models.JSONField(default=dict, blank=True)
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    source = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        ordering = ["-event_date"]
        indexes = [
            models.Index(fields=["symbol", "event_type", "event_date"]),
        ]

    def __str__(self):
        ticker = self.symbol.ticker if self.symbol else "MARKET"
        return f"{ticker} {self.event_type} {self.event_date}"


class NewsArticle(models.Model):
    class Sentiment(models.TextChoices):
        POSITIVE = "POSITIVE", "Positive"
        NEUTRAL = "NEUTRAL", "Neutral"
        NEGATIVE = "NEGATIVE", "Negative"

    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="news_articles")
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, blank=True, default="")
    source = models.CharField(max_length=100, blank=True, default="")
    published_at = models.DateTimeField(db_index=True)
    sentiment = models.CharField(
        max_length=20,
        choices=Sentiment.choices,
        default=Sentiment.NEUTRAL,
    )
    summary = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["symbol", "published_at"]),
        ]

    def __str__(self):
        return f"{self.symbol.ticker}: {self.title[:60]}"
