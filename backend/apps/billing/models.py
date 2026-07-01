"""Billing domain: plans, subscriptions, invoices, and payment methods."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.billing.constants import InvoiceStatus, PlanInterval, SubscriptionStatus
from common.mixins import BaseModel


def default_features() -> dict[str, object]:
    return {}


class Plan(BaseModel):
    """A subscription tier. ``features`` holds entitlement limits/flags."""

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    price_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="USD")
    interval = models.CharField(
        max_length=10, choices=PlanInterval.choices, default=PlanInterval.MONTH
    )
    trial_days = models.PositiveIntegerField(default=0)
    tier = models.PositiveSmallIntegerField(default=0)  # ordering / comparison
    features = models.JSONField(default=default_features, blank=True)
    # RBAC role granted while this plan is active ("" = none).
    role_name = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "billing_plans"
        ordering = ["tier", "price_cents"]

    def __str__(self) -> str:
        return self.code


class Subscription(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(
        max_length=12, choices=SubscriptionStatus.choices, default=SubscriptionStatus.ACTIVE
    )
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    provider = models.CharField(max_length=30, default="mock")
    provider_subscription_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "billing_subscriptions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"], name="sub_user_status_idx"),
            models.Index(fields=["status", "current_period_end"], name="sub_status_period_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.plan_id}:{self.status}"


class Invoice(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices"
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=10, choices=InvoiceStatus.choices, default=InvoiceStatus.OPEN
    )
    description = models.CharField(max_length=255, blank=True)
    provider = models.CharField(max_length=30, default="mock")
    provider_invoice_id = models.CharField(max_length=255, blank=True)
    provider_payment_id = models.CharField(max_length=255, blank=True)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "billing_invoices"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"], name="invoice_user_time_idx")]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.amount_cents}:{self.status}"


class PaymentMethod(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods"
    )
    provider = models.CharField(max_length=30, default="mock")
    provider_payment_method_id = models.CharField(max_length=255, blank=True)
    brand = models.CharField(max_length=30, default="mock")
    last4 = models.CharField(max_length=4, blank=True)
    exp_month = models.PositiveSmallIntegerField(null=True, blank=True)
    exp_year = models.PositiveSmallIntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "billing_payment_methods"
        ordering = ["-is_default", "-created_at"]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.brand}:{self.last4}"
