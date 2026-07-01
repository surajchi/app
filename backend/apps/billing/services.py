"""Billing write-side: subscribe, cancel, renew, refund, and entitlements.

Paid tiers grant an RBAC role (``plan.role_name``) while active; cancellation /
expiry revokes it. Charges go through the pluggable payment provider ACL.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone

from apps.billing.constants import (
    LIVE_STATUSES,
    InvoiceStatus,
    SubscriptionStatus,
    interval_delta,
)
from apps.billing.models import Invoice, Plan, Subscription
from apps.rbac.services import assign_role, remove_role
from integrations.payments.registry import get_payment_provider

if TYPE_CHECKING:
    from apps.users.models import User

logger = logging.getLogger("finpulse")


class PaymentError(Exception):
    """Raised when a provider charge is declined."""


def free_plan() -> Plan | None:
    return Plan.objects.filter(price_cents=0, is_active=True).order_by("tier").first()


def current_subscription(user: User) -> Subscription | None:
    return (
        user.subscriptions.filter(status__in=list(LIVE_STATUSES))
        .select_related("plan")
        .order_by("-created_at")
        .first()
    )


def _has_paid_history(user: User) -> bool:
    return Subscription.objects.filter(user=user, plan__price_cents__gt=0).exists()


def _record_invoice(
    *,
    user: User,
    subscription: Subscription,
    amount_cents: int,
    currency: str,
    provider: str,
    provider_invoice_id: str,
    provider_payment_id: str,
    description: str,
) -> Invoice:
    return Invoice.objects.create(
        user=user,
        subscription=subscription,
        amount_cents=amount_cents,
        currency=currency,
        status=InvoiceStatus.PAID,
        description=description,
        provider=provider,
        provider_invoice_id=provider_invoice_id,
        provider_payment_id=provider_payment_id,
        period_start=subscription.current_period_start,
        period_end=subscription.current_period_end,
        paid_at=timezone.now(),
    )


def _apply_role(user: User, prev_role: str, new_role: str) -> None:
    if prev_role and prev_role != new_role:
        remove_role(user, prev_role)
    if new_role:
        assign_role(user, new_role)


@transaction.atomic
def subscribe(*, user: User, plan: Plan, start_trial: bool = False) -> Subscription:
    provider = get_payment_provider()
    now = timezone.now()

    existing = current_subscription(user)
    prev_role = existing.plan.role_name if existing else ""
    trial_eligible = start_trial and plan.trial_days > 0 and not _has_paid_history(user)

    if existing:
        existing.status = SubscriptionStatus.CANCELED
        existing.canceled_at = now
        existing.save(update_fields=["status", "canceled_at", "updated_at"])

    sub = Subscription(user=user, plan=plan, provider=provider.name, current_period_start=now)
    charge = None

    if plan.price_cents == 0:
        sub.status = SubscriptionStatus.ACTIVE
        sub.current_period_end = None  # free never expires
    elif trial_eligible:
        sub.status = SubscriptionStatus.TRIALING
        sub.trial_end = now + timedelta(days=plan.trial_days)
        sub.current_period_end = sub.trial_end
        sub.provider_subscription_id = provider.create_subscription(
            user_ref=str(user.id),
            plan_code=plan.code,
            amount_cents=plan.price_cents,
            currency=plan.currency,
        ).provider_subscription_id
    else:
        charge = provider.charge(
            user_ref=str(user.id),
            amount_cents=plan.price_cents,
            currency=plan.currency,
            description=f"{plan.name} subscription",
        )
        if not charge.ok:
            raise PaymentError(charge.error or "Payment was declined.")
        sub.status = SubscriptionStatus.ACTIVE
        sub.current_period_end = now + interval_delta(plan.interval)
        sub.provider_subscription_id = provider.create_subscription(
            user_ref=str(user.id),
            plan_code=plan.code,
            amount_cents=plan.price_cents,
            currency=plan.currency,
        ).provider_subscription_id

    sub.save()

    if charge is not None:
        _record_invoice(
            user=user,
            subscription=sub,
            amount_cents=plan.price_cents,
            currency=plan.currency,
            provider=provider.name,
            provider_invoice_id=charge.provider_invoice_id,
            provider_payment_id=charge.provider_payment_id,
            description=f"{plan.name} subscription",
        )

    _apply_role(user, prev_role, plan.role_name)
    logger.info(
        "billing.subscribed",
        extra={"user": str(user.id), "plan": plan.code, "status": sub.status},
    )
    return sub


@transaction.atomic
def cancel(*, user: User, at_period_end: bool = True) -> Subscription:
    sub = current_subscription(user)
    if sub is None:
        raise PaymentError("No active subscription to cancel.")

    if at_period_end and sub.current_period_end is not None:
        sub.cancel_at_period_end = True
        sub.save(update_fields=["cancel_at_period_end", "updated_at"])
    else:
        provider = get_payment_provider()
        if sub.provider_subscription_id:
            provider.cancel_subscription(sub.provider_subscription_id)
        sub.status = SubscriptionStatus.CANCELED
        sub.canceled_at = timezone.now()
        sub.save(update_fields=["status", "canceled_at", "updated_at"])
        if sub.plan.role_name:
            remove_role(user, sub.plan.role_name)
    return sub


def refund_invoice(*, invoice: Invoice) -> Invoice:
    provider = get_payment_provider()
    if invoice.provider_payment_id:
        provider.refund(invoice.provider_payment_id, invoice.amount_cents)
    invoice.status = InvoiceStatus.REFUNDED
    invoice.save(update_fields=["status", "updated_at"])
    return invoice


def entitlements(user: User) -> dict[str, Any]:
    sub = current_subscription(user)
    plan = sub.plan if sub else free_plan()
    return {
        "plan": plan.code if plan else "free",
        "status": sub.status if sub else "none",
        "features": plan.features if plan else {},
        "current_period_end": (
            sub.current_period_end.isoformat() if sub and sub.current_period_end else None
        ),
        "cancel_at_period_end": sub.cancel_at_period_end if sub else False,
    }


def _expire(sub: Subscription) -> None:
    sub.status = SubscriptionStatus.EXPIRED
    sub.canceled_at = sub.canceled_at or timezone.now()
    sub.save(update_fields=["status", "canceled_at", "updated_at"])
    if sub.plan.role_name:
        remove_role(sub.user, sub.plan.role_name)


@transaction.atomic
def process_renewals() -> dict[str, int]:
    """Renew due paid subscriptions and expire those flagged to cancel."""
    now = timezone.now()
    provider = get_payment_provider()
    due = Subscription.objects.filter(
        status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING],
        current_period_end__isnull=False,
        current_period_end__lte=now,
    ).select_related("plan", "user")

    renewed = expired = past_due = 0
    for sub in due:
        if sub.cancel_at_period_end:
            _expire(sub)
            expired += 1
            continue

        charge = provider.charge(
            user_ref=str(sub.user_id),
            amount_cents=sub.plan.price_cents,
            currency=sub.plan.currency,
            description=f"{sub.plan.name} renewal",
        )
        if charge.ok:
            sub.current_period_start = sub.current_period_end
            sub.current_period_end = sub.current_period_end + interval_delta(sub.plan.interval)
            sub.status = SubscriptionStatus.ACTIVE
            sub.trial_end = None
            sub.save(
                update_fields=[
                    "current_period_start",
                    "current_period_end",
                    "status",
                    "trial_end",
                    "updated_at",
                ]
            )
            _record_invoice(
                user=sub.user,
                subscription=sub,
                amount_cents=sub.plan.price_cents,
                currency=sub.plan.currency,
                provider=provider.name,
                provider_invoice_id=charge.provider_invoice_id,
                provider_payment_id=charge.provider_payment_id,
                description=f"{sub.plan.name} renewal",
            )
            renewed += 1
        else:
            sub.status = SubscriptionStatus.PAST_DUE
            sub.save(update_fields=["status", "updated_at"])
            past_due += 1

    logger.info(
        "billing.renewals_processed",
        extra={"renewed": renewed, "expired": expired, "past_due": past_due},
    )
    return {"renewed": renewed, "expired": expired, "past_due": past_due}


def handle_webhook_event(event: dict[str, Any]) -> bool:
    """Process a provider webhook event. Returns True if handled."""
    event_type = event.get("type", "")
    provider_sub_id = event.get("subscription_id", "")

    if event_type == "subscription.canceled" and provider_sub_id:
        sub = Subscription.objects.filter(
            provider_subscription_id=provider_sub_id, status__in=list(LIVE_STATUSES)
        ).first()
        if sub:
            sub.status = SubscriptionStatus.CANCELED
            sub.canceled_at = timezone.now()
            sub.save(update_fields=["status", "canceled_at", "updated_at"])
            if sub.plan.role_name:
                remove_role(sub.user, sub.plan.role_name)
            return True
    return False
