from __future__ import annotations

from django.contrib import admin

from apps.econcalendar.models import EconomicEvent


@admin.register(EconomicEvent)
class EconomicEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_time",
        "currency",
        "title",
        "importance",
        "actual",
        "forecast",
        "previous",
    )
    list_filter = ("importance", "currency", "category")
    search_fields = ("title", "currency")
    date_hierarchy = "event_time"
