"""Admin registrations for portfolios, holdings, and transactions."""

from __future__ import annotations

from django.contrib import admin

from apps.portfolios.models import Holding, Portfolio, Transaction


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "base_currency", "is_default", "created_at")
    list_filter = ("is_default", "base_currency")
    search_fields = ("name", "user__email")


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "instrument", "quantity", "avg_cost", "realized_pnl")
    search_fields = ("portfolio__name", "instrument__symbol")
    autocomplete_fields = ("portfolio", "instrument")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "instrument", "type", "quantity", "price", "executed_at")
    list_filter = ("type",)
    search_fields = ("portfolio__name", "instrument__symbol")
    autocomplete_fields = ("portfolio", "instrument")
