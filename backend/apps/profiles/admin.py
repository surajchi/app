from django.contrib import admin

from apps.profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "country", "base_currency", "language", "experience_level")
    list_filter = ("experience_level", "risk_appetite", "base_currency")
    search_fields = ("user__email", "user__full_name")
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
