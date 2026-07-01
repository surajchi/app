"""Billing enums and interval helpers."""

from __future__ import annotations

from datetime import timedelta

from django.db import models


class PlanInterval(models.TextChoices):
    MONTH = "month", "Monthly"
    YEAR = "year", "Yearly"


class SubscriptionStatus(models.TextChoices):
    TRIALING = "trialing", "Trialing"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past due"
    CANCELED = "canceled", "Canceled"
    EXPIRED = "expired", "Expired"


# Statuses that count as a usable, current subscription.
LIVE_STATUSES = (
    SubscriptionStatus.TRIALING,
    SubscriptionStatus.ACTIVE,
    SubscriptionStatus.PAST_DUE,
)


class InvoiceStatus(models.TextChoices):
    PAID = "paid", "Paid"
    OPEN = "open", "Open"
    FAILED = "failed", "Failed"
    VOID = "void", "Void"
    REFUNDED = "refunded", "Refunded"


def interval_delta(interval: str) -> timedelta:
    return timedelta(days=365) if interval == PlanInterval.YEAR else timedelta(days=30)
