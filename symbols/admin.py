from django.contrib import admin

from symbols.models import Company, IndexMembership, Sector, Symbol


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "index_symbol")
    search_fields = ("name",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "isin", "sector")
    list_filter = ("sector",)
    search_fields = ("name", "isin")


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ("id", "ticker", "exchange", "company", "is_active", "instrument_token")
    list_filter = ("exchange", "is_active")
    search_fields = ("ticker", "company__name")


@admin.register(IndexMembership)
class IndexMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "symbol", "index_name")
    list_filter = ("index_name",)
    search_fields = ("symbol__ticker",)
