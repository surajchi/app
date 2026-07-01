"""Notification, per-channel delivery log, and user preferences."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.notifications.constants import (
    Channel,
    DeliveryStatus,
    NotificationType,
    Priority,
    default_channels,
    default_quiet_hours,
)
from common.mixins import BaseModel, TimeStampedModel


class Notification(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="notif_user_time_idx"),
            models.Index(
                fields=["user"],
                name="notif_user_unread_idx",
                condition=models.Q(read_at__isnull=True),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.type}:{self.title[:30]}"


class NotificationDelivery(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="deliveries"
    )
    channel = models.CharField(max_length=10, choices=Channel.choices)
    status = models.CharField(
        max_length=10, choices=DeliveryStatus.choices, default=DeliveryStatus.QUEUED
    )
    provider_message_id = models.CharField(max_length=255, blank=True)
    error = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notification_deliveries"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.notification_id}:{self.channel}:{self.status}"


class NotificationPreference(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_prefs"
    )
    channels = models.JSONField(default=default_channels)
    quiet_hours = models.JSONField(default=default_quiet_hours, blank=True)
    digest = models.CharField(max_length=10, default="off")  # off | daily | weekly
    marketing_opt_in = models.BooleanField(default=False)

    class Meta:
        db_table = "notification_preferences"

    def __str__(self) -> str:
        return f"prefs<{self.user_id}>"
