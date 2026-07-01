"""Alert rule + fired-alert serializers with per-trigger condition validation."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.alerts.constants import PRICE_TRIGGERS, TriggerType
from apps.alerts.models import Alert, AlertRule
from apps.notifications.constants import Channel, Priority

_VALID_CHANNELS = {str(c) for c in Channel.values}
_VALID_PRIORITIES = {str(p) for p in Priority.values}
_SENTIMENT_LABELS = {"positive", "negative", "neutral"}


class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = [
            "id",
            "name",
            "instrument",
            "trigger_type",
            "condition",
            "frequency",
            "cooldown_seconds",
            "channels",
            "priority",
            "is_active",
            "last_triggered_at",
            "expires_at",
            "created_at",
        ]
        read_only_fields = ["id", "last_triggered_at", "created_at"]

    def validate_channels(self, value: list[str]) -> list[str]:
        bad = [c for c in value if c not in _VALID_CHANNELS]
        if bad:
            raise serializers.ValidationError(f"Unknown channels: {bad}")
        return value

    def validate_priority(self, value: str) -> str:
        if value not in _VALID_PRIORITIES:
            raise serializers.ValidationError(
                f"Priority must be one of {sorted(_VALID_PRIORITIES)}."
            )
        return value

    def _current(self, attrs: dict[str, Any], field: str, default: Any = None) -> Any:
        if field in attrs:
            return attrs[field]
        return getattr(self.instance, field, default)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        trigger = self._current(attrs, "trigger_type")
        condition = self._current(attrs, "condition", {}) or {}
        instrument = self._current(attrs, "instrument")

        if trigger in PRICE_TRIGGERS:
            if instrument is None:
                raise serializers.ValidationError(
                    {"instrument": "Price alerts require an instrument."}
                )
            value = condition.get("value")
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise serializers.ValidationError({"condition": "Provide a numeric 'value'."})
            if trigger == TriggerType.PCT_CHANGE and value <= 0:
                raise serializers.ValidationError(
                    {"condition": "'value' must be > 0 for pct_change."}
                )
        elif trigger == TriggerType.NEWS_KEYWORD:
            if not str(condition.get("keyword", "")).strip():
                raise serializers.ValidationError({"condition": "Provide a non-empty 'keyword'."})
        elif trigger == TriggerType.SENTIMENT:
            if condition.get("label") not in _SENTIMENT_LABELS:
                raise serializers.ValidationError(
                    {"condition": "Provide 'label' in positive|negative|neutral."}
                )
        return attrs


class AlertSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source="rule.name", read_only=True)
    trigger_type = serializers.CharField(source="rule.trigger_type", read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id",
            "rule",
            "rule_name",
            "trigger_type",
            "snapshot",
            "status",
            "triggered_at",
        ]
        read_only_fields = fields
