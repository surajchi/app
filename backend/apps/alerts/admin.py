"""Admin registrations for alert rules and fired-alert history."""

from __future__ import annotations

from django.contrib import admin

from apps.alerts.models import Alert, AlertRule


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "trigger_type",
        "is_active",
        "frequency",
        "last_triggered_at",
    )
    list_filter = ("trigger_type", "is_active", "frequency")
    search_fields = ("name", "user__email")
    autocomplete_fields = ("user", "instrument")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("rule", "user", "status", "triggered_at")
    list_filter = ("status",)
    search_fields = ("rule__name", "user__email")
    readonly_fields = ("triggered_at",)
