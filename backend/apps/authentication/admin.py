from django.contrib import admin

from apps.authentication.models import OAuthAccount, OTPCode, TwoFactor


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("target", "purpose", "channel", "attempts", "consumed_at", "expires_at")
    list_filter = ("purpose", "channel")
    search_fields = ("target",)
    readonly_fields = ("code_hash",)


@admin.register(TwoFactor)
class TwoFactorAdmin(admin.ModelAdmin):
    list_display = ("user", "is_enabled", "confirmed_at")
    list_filter = ("is_enabled",)
    search_fields = ("user__email",)
    readonly_fields = ("secret", "recovery_codes")
    list_select_related = ("user",)


@admin.register(OAuthAccount)
class OAuthAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "email", "created_at")
    list_filter = ("provider",)
    search_fields = ("user__email", "email", "provider_uid")
    list_select_related = ("user",)
