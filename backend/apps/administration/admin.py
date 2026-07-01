"""Admin registration for the audit log (read-only)."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from apps.administration.models import AdminAuditLog


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_type", "target_id", "ip", "created_at")
    list_filter = ("action", "target_type")
    search_fields = ("actor__email", "target_id", "action")
    readonly_fields = (
        "actor",
        "action",
        "target_type",
        "target_id",
        "metadata",
        "ip",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return False
