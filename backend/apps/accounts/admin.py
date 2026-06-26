from django.contrib import admin

from apps.accounts.models import Device, LoginHistory, UserSession


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "device_name", "is_trusted", "last_seen_at")
    list_filter = ("platform", "is_trusted")
    search_fields = ("user__email", "device_name")
    list_select_related = ("user",)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "ip", "is_active", "created_at", "expires_at", "revoked_at")
    search_fields = ("user__email", "jti", "ip")
    list_select_related = ("user", "device")
    readonly_fields = ("jti",)


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "success", "ip", "created_at")
    list_filter = ("event", "success")
    search_fields = ("user__email", "ip")
    list_select_related = ("user",)
