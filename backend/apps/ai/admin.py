from django.contrib import admin

from apps.ai.models import AIPrediction


@admin.register(AIPrediction)
class AIPredictionAdmin(admin.ModelAdmin):
    list_display = ("instrument", "prediction_type", "horizon", "confidence", "model", "created_at")
    list_filter = ("prediction_type", "model")
    search_fields = ("instrument__symbol",)
    list_select_related = ("instrument",)
    readonly_fields = ("value",)
