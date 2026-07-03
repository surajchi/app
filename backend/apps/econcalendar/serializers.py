from __future__ import annotations

from rest_framework import serializers

from apps.econcalendar.models import EconomicEvent


class EconomicEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EconomicEvent
        fields = (
            "id",
            "title",
            "country",
            "currency",
            "importance",
            "category",
            "event_time",
            "actual",
            "forecast",
            "previous",
            "unit",
        )
        read_only_fields = fields
