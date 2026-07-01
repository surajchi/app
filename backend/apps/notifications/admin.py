from django.contrib import admin

from apps.notifications.models import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
)


class DeliveryInline(admin.TabularInline):
    model = NotificationDelivery
    extra = 0
    readonly_fields = ("channel", "status", "attempts", "provider_message_id", "error", "sent_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "type", "priority", "read_at", "created_at")
    list_filter = ("type", "priority")
    search_fields = ("title", "user__email")
    list_select_related = ("user",)
    inlines = (DeliveryInline,)


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("notification", "channel", "status", "attempts", "sent_at")
    list_filter = ("channel", "status")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "digest", "marketing_opt_in")
    search_fields = ("user__email",)
