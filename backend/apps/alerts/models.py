"""Alert rules (user-defined triggers) and fired-alert history."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.alerts.constants import AlertStatus, Frequency, TriggerType
from apps.markets.models import Instrument
from common.mixins import BaseModel, TimeStampedModel


class AlertRule(BaseModel):
    """A user-defined condition that fires a notification when met.

    ``condition`` shape depends on ``trigger_type``:
      price_above / price_below -> {"value": <number>}
      pct_change                -> {"value": <positive percent>}
      news_keyword              -> {"keyword": "<text>"}
      sentiment                 -> {"label": "positive|negative|neutral"}
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alert_rules"
    )
    name = models.CharField(max_length=120)
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="alert_rules",
    )
    trigger_type = models.CharField(max_length=20, choices=TriggerType.choices)
    condition = models.JSONField(default=dict, blank=True)
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.ONCE)
    cooldown_seconds = models.PositiveIntegerField(default=0)
    # Channel override; empty list -> notification type defaults from preferences.
    channels = models.JSONField(default=list, blank=True)
    priority = models.CharField(max_length=10, default="high")
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "alert_rules"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"], name="alertrule_user_active_idx"),
            models.Index(fields=["trigger_type", "is_active"], name="alertrule_trigger_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.name}:{self.trigger_type}"


class Alert(TimeStampedModel):
    """A single firing of an AlertRule (history + audit trail)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="fires")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts"
    )
    triggered_at = models.DateTimeField(auto_now_add=True, db_index=True)
    snapshot = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=12, choices=AlertStatus.choices, default=AlertStatus.SENT)
    notification = models.ForeignKey(
        "notifications.Notification",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "alerts"
        ordering = ["-triggered_at"]
        indexes = [
            models.Index(fields=["user", "-triggered_at"], name="alert_user_time_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.rule_id}@{self.triggered_at}"
