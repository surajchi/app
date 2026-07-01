"""Notification enums + default per-type channel preferences."""

from __future__ import annotations

from django.db import models


class NotificationType(models.TextChoices):
    ALERT = "alert", "Alert"
    NEWS = "news", "News"
    SYSTEM = "system", "System"
    BILLING = "billing", "Billing"
    AI = "ai", "AI"
    MARKETING = "marketing", "Marketing"


class Priority(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class Channel(models.TextChoices):
    IN_APP = "in_app", "In-app"
    EMAIL = "email", "Email"
    PUSH = "push", "Push"
    TELEGRAM = "telegram", "Telegram"
    SMS = "sms", "SMS"


class DeliveryStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    RETRYING = "retrying", "Retrying"
    SKIPPED = "skipped", "Skipped"


# Default channel matrix per notification type.
DEFAULT_CHANNELS: dict[str, list[str]] = {
    "alert": ["in_app", "push", "email"],
    "news": ["in_app", "push"],
    "system": ["in_app", "email"],
    "billing": ["in_app", "email"],
    "ai": ["in_app"],
    "marketing": ["email"],
}


def default_channels() -> dict[str, list[str]]:
    return {k: list(v) for k, v in DEFAULT_CHANNELS.items()}


def default_quiet_hours() -> dict:
    # Disabled by default; e.g. {"start": "22:00", "end": "07:00"} to enable.
    return {}
