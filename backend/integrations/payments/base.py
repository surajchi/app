"""Provider-agnostic payment interface (anti-corruption layer).

A real gateway (Stripe, Razorpay, …) can implement ``PaymentProvider`` and be
registered without changing any billing domain code.
"""

from __future__ import annotations

import dataclasses
from typing import Protocol, runtime_checkable


@dataclasses.dataclass(frozen=True)
class ChargeResult:
    ok: bool
    provider_payment_id: str = ""
    provider_invoice_id: str = ""
    error: str = ""


@dataclasses.dataclass(frozen=True)
class ProviderSubscription:
    provider_subscription_id: str
    status: str


@runtime_checkable
class PaymentProvider(Protocol):
    name: str

    def charge(
        self, *, user_ref: str, amount_cents: int, currency: str, description: str
    ) -> ChargeResult: ...

    def create_subscription(
        self, *, user_ref: str, plan_code: str, amount_cents: int, currency: str
    ) -> ProviderSubscription: ...

    def cancel_subscription(self, provider_subscription_id: str) -> bool: ...

    def refund(self, provider_payment_id: str, amount_cents: int) -> ChargeResult: ...

    def verify_webhook(self, payload: bytes, signature: str | None) -> bool: ...
