from django.contrib import admin

from market_data.models import (
    CorporateEvent,
    DeliveryDaily,
    FIIDIIActivity,
    NewsArticle,
    OHLCVDaily,
    SectorPerformance,
)


@admin.register(OHLCVDaily)
class OHLCVDailyAdmin(admin.ModelAdmin):
    list_display = ("symbol", "date", "close", "volume")
    list_filter = ("date",)
    search_fields = ("symbol__ticker",)
    date_hierarchy = "date"


@admin.register(DeliveryDaily)
class DeliveryDailyAdmin(admin.ModelAdmin):
    list_display = ("symbol", "date", "delivery_pct", "delivery_qty")
    search_fields = ("symbol__ticker",)
    date_hierarchy = "date"


@admin.register(FIIDIIActivity)
class FIIDIIActivityAdmin(admin.ModelAdmin):
    list_display = ("date", "fii_net", "dii_net")
    date_hierarchy = "date"


@admin.register(SectorPerformance)
class SectorPerformanceAdmin(admin.ModelAdmin):
    list_display = ("sector", "date", "return_1d", "return_20d")
    list_filter = ("sector",)
    date_hierarchy = "date"


@admin.register(CorporateEvent)
class CorporateEventAdmin(admin.ModelAdmin):
    list_display = ("symbol", "event_type", "event_date", "severity", "title")
    list_filter = ("event_type", "severity")
    search_fields = ("symbol__ticker", "title")
    date_hierarchy = "event_date"


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("symbol", "title", "published_at", "sentiment", "source")
    list_filter = ("sentiment", "source")
    search_fields = ("symbol__ticker", "title")
