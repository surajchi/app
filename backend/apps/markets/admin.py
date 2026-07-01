from django.contrib import admin

from apps.markets.models import (
    DataProviderStatus,
    Exchange,
    Instrument,
    Market,
    SymbolAlias,
)


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "asset_class", "region")
    search_fields = ("code", "name")


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country", "currency", "is_active")
    list_filter = ("is_active", "country")
    search_fields = ("code", "name")


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ("symbol", "asset_class", "name", "exchange", "currency", "is_active")
    list_filter = ("asset_class", "is_active")
    search_fields = ("symbol", "name")
    list_select_related = ("exchange",)
    autocomplete_fields = ("exchange",)


@admin.register(SymbolAlias)
class SymbolAliasAdmin(admin.ModelAdmin):
    list_display = ("provider", "provider_symbol", "instrument")
    search_fields = ("provider_symbol", "instrument__symbol")
    list_select_related = ("instrument",)


@admin.register(DataProviderStatus)
class DataProviderStatusAdmin(admin.ModelAdmin):
    list_display = ("provider", "domain", "status", "quota_used", "last_success_at")
    list_filter = ("status", "domain")
