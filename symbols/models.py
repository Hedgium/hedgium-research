from django.db import models


class Sector(models.Model):
    name = models.CharField(max_length=100, unique=True)
    index_symbol = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Company(models.Model):
    name = models.CharField(max_length=255)
    isin = models.CharField(max_length=12, blank=True, default="", db_index=True)
    sector = models.ForeignKey(
        Sector,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="companies",
    )

    class Meta:
        verbose_name_plural = "companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Symbol(models.Model):
    class Exchange(models.TextChoices):
        NSE = "NSE", "NSE"
        BSE = "BSE", "BSE"

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="symbols")
    ticker = models.CharField(max_length=20, db_index=True)
    exchange = models.CharField(max_length=10, choices=Exchange.choices, default=Exchange.NSE)
    instrument_token = models.BigIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("ticker", "exchange")]
        ordering = ["ticker"]

    def __str__(self):
        return f"{self.ticker}.{self.exchange}"


class IndexMembership(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="index_memberships")
    index_name = models.CharField(max_length=50, db_index=True)

    class Meta:
        unique_together = [("symbol", "index_name")]

    def __str__(self):
        return f"{self.symbol.ticker} in {self.index_name}"
