"""Free, self-contained mock payment provider.

Deterministic and keyless — approves any non-negative charge — so the full
billing flow works in dev/CI without a real gateway. Swap in a real provider
via ``PAYMENT_PROVIDER`` when going live.
"""

from __future__ import annotations

import uuid

from django.conf import settings

from integrations.payments.base import ChargeResult, ProviderSubscription


class MockPaymentProvider:
    name = "mock"

    def charge(
        self, *, user_ref: str, amount_cents: int, currency: str, description: str
    ) -> ChargeResult:
        if amount_cents < 0:
            return ChargeResult(ok=False, error="Invalid amount.")
        token = uuid.uuid4().hex
        return ChargeResult(
            ok=True,
            provider_payment_id=f"mock_pay_{token}",
            provider_invoice_id=f"mock_inv_{token}",
        )

    def create_subscription(
        self, *, user_ref: str, plan_code: str, amount_cents: int, currency: str
    ) -> ProviderSubscription:
        return ProviderSubscription(
            provider_subscription_id=f"mock_sub_{uuid.uuid4().hex}", status="active"
        )

    def cancel_subscription(self, provider_subscription_id: str) -> bool:
        return True

    def refund(self, provider_payment_id: str, amount_cents: int) -> ChargeResult:
        return ChargeResult(ok=True, provider_payment_id=f"mock_ref_{uuid.uuid4().hex}")

    def verify_webhook(self, payload: bytes, signature: str | None) -> bool:
        secret = getattr(settings, "PAYMENT_WEBHOOK_SECRET", "")
        # No configured secret (dev/mock) -> accept. Otherwise require a match.
        return not secret or signature == secret
