"""Resolve the active payment provider (defaults to the free mock provider)."""

from __future__ import annotations

from django.conf import settings

from integrations.payments.base import PaymentProvider
from integrations.payments.mock import MockPaymentProvider

_PROVIDERS: dict[str, type] = {
    "mock": MockPaymentProvider,
}


def get_payment_provider(name: str | None = None) -> PaymentProvider:
    name = name or getattr(settings, "PAYMENT_PROVIDER", "mock")
    provider_cls = _PROVIDERS.get(str(name), MockPaymentProvider)
    return provider_cls()
