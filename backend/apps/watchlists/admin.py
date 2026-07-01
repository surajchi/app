"""Admin registrations for watchlists."""

from __future__ import annotations

from django.contrib import admin

from apps.watchlists.models import Watchlist, WatchlistItem


class WatchlistItemInline(admin.TabularInline):
    model = WatchlistItem
    extra = 0
    autocomplete_fields = ("instrument",)


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_default", "created_at")
    list_filter = ("is_default",)
    search_fields = ("name", "user__email")
    inlines = [WatchlistItemInline]


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ("watchlist", "instrument", "position")
    search_fields = ("watchlist__name", "instrument__symbol")
    autocomplete_fields = ("watchlist", "instrument")
