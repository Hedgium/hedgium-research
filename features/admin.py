from django.contrib import admin

from features.models import FeatureSnapshot, FundamentalMetric


@admin.register(FundamentalMetric)
class FundamentalMetricAdmin(admin.ModelAdmin):
    list_display = (
        "symbol",
        "period_end",
        "pe",
        "pb",
        "roe",
        "debt_equity",
        "source",
    )
    list_filter = ("source",)
    search_fields = ("symbol__ticker",)


@admin.register(FeatureSnapshot)
class FeatureSnapshotAdmin(admin.ModelAdmin):
    list_display = ("symbol", "as_of_date", "feature_group")
    list_filter = ("feature_group", "as_of_date")
    search_fields = ("symbol__ticker",)
    readonly_fields = ("features",)
