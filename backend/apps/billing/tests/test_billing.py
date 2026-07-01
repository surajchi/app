from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing import services
from apps.billing.models import Invoice, PaymentMethod, Plan, Subscription
from apps.rbac.services import assign_role, user_role_names
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _superuser():
    user = UserFactory()
    user.is_superuser = True
    user.is_staff = True
    user.save()
    return user


def _plan(code: str) -> Plan:
    return Plan.objects.get(code=code)


# --- plans ------------------------------------------------------------------


def test_plans_are_public_and_seeded(client):
    data = client.get("/api/v1/billing/plans/").json()["data"]
    codes = {p["code"] for p in data}
    assert {"free", "premium", "pro"} <= codes
    premium = next(p for p in data if p["code"] == "premium")
    assert premium["price"] == 9.99
    assert premium["features"]["max_alerts"] == 50


# --- subscribe --------------------------------------------------------------


def test_subscribe_requires_auth(client):
    assert client.post("/api/v1/billing/subscribe/", {"plan": "premium"}).status_code == 401


def test_subscribe_charges_and_grants_role(client):
    user = UserFactory()
    client.force_authenticate(user)
    resp = client.post("/api/v1/billing/subscribe/", {"plan": "premium"}, format="json")
    assert resp.status_code == 201, resp.content
    assert resp.json()["data"]["status"] == "active"

    sub = services.current_subscription(user)
    assert sub is not None and sub.plan.code == "premium"
    assert Invoice.objects.filter(user=user, status="paid").count() == 1
    assert "premium" in user_role_names(user)


def test_subscribe_with_trial_skips_charge(client):
    user = UserFactory()
    sub = services.subscribe(user=user, plan=_plan("premium"), start_trial=True)
    assert sub.status == "trialing"
    assert sub.trial_end is not None
    assert Invoice.objects.filter(user=user).count() == 0
    assert "premium" in user_role_names(user)


def test_upgrade_replaces_previous_subscription(client):
    user = UserFactory()
    services.subscribe(user=user, plan=_plan("premium"))
    services.subscribe(user=user, plan=_plan("pro"))

    current = services.current_subscription(user)
    assert current.plan.code == "pro"
    # Old subscription is closed out; only one live subscription remains.
    live = Subscription.objects.filter(user=user, status__in=["active", "trialing", "past_due"])
    assert live.count() == 1
    assert Invoice.objects.filter(user=user, status="paid").count() == 2


def test_downgrade_to_free_revokes_role(client):
    user = UserFactory()
    services.subscribe(user=user, plan=_plan("premium"))
    assert "premium" in user_role_names(user)
    services.subscribe(user=user, plan=_plan("free"))
    assert "premium" not in user_role_names(user)


# --- cancel -----------------------------------------------------------------


def test_cancel_at_period_end_keeps_access(client):
    user = UserFactory()
    client.force_authenticate(user)
    services.subscribe(user=user, plan=_plan("premium"))
    resp = client.post("/api/v1/billing/cancel/", {"at_period_end": True}, format="json")
    assert resp.status_code == 200
    sub = services.current_subscription(user)
    assert sub.cancel_at_period_end is True and sub.status == "active"
    assert "premium" in user_role_names(user)


def test_cancel_immediately_revokes_role(client):
    user = UserFactory()
    client.force_authenticate(user)
    services.subscribe(user=user, plan=_plan("premium"))
    resp = client.post("/api/v1/billing/cancel/", {"at_period_end": False}, format="json")
    assert resp.status_code == 200
    assert services.current_subscription(user) is None
    assert "premium" not in user_role_names(user)


def test_cancel_without_subscription_400(client):
    user = UserFactory()
    client.force_authenticate(user)
    assert client.post("/api/v1/billing/cancel/", {}, format="json").status_code == 400


# --- subscription + entitlements --------------------------------------------


def test_entitlements_default_to_free(client):
    user = UserFactory()
    client.force_authenticate(user)
    data = client.get("/api/v1/billing/subscription/").json()["data"]
    assert data["subscription"] is None
    assert data["entitlements"]["plan"] == "free"
    assert data["entitlements"]["features"]["max_alerts"] == 5


def test_entitlements_reflect_active_plan(client):
    user = UserFactory()
    client.force_authenticate(user)
    services.subscribe(user=user, plan=_plan("premium"))
    data = client.get("/api/v1/billing/subscription/").json()["data"]
    assert data["entitlements"]["plan"] == "premium"
    assert data["entitlements"]["features"]["realtime"] is True


# --- invoices + payment methods ---------------------------------------------


def test_invoice_list(client):
    user = UserFactory()
    client.force_authenticate(user)
    services.subscribe(user=user, plan=_plan("premium"))
    data = client.get("/api/v1/billing/invoices/").json()["data"]
    assert len(data) == 1 and data[0]["status"] == "paid"


def test_add_payment_method_and_default(client):
    user = UserFactory()
    client.force_authenticate(user)
    first = client.post(
        "/api/v1/billing/payment-methods/",
        {"last4": "4242", "exp_month": 12, "exp_year": 2030},
        format="json",
    )
    assert first.status_code == 201
    second = client.post(
        "/api/v1/billing/payment-methods/",
        {"last4": "1111", "exp_month": 1, "exp_year": 2031, "make_default": True},
        format="json",
    )
    assert second.status_code == 201
    defaults = PaymentMethod.objects.filter(user=user, is_default=True)
    assert defaults.count() == 1 and defaults.first().last4 == "1111"


# --- renewals ---------------------------------------------------------------


def test_process_renewals_renews_due_paid_subscription():
    user = UserFactory()
    now = timezone.now()
    sub = Subscription.objects.create(
        user=user,
        plan=_plan("premium"),
        status="active",
        current_period_start=now - timedelta(days=40),
        current_period_end=now - timedelta(days=1),
        provider="mock",
        provider_subscription_id="mock_sub_x",
    )
    result = services.process_renewals()
    assert result["renewed"] == 1
    sub.refresh_from_db()
    assert sub.status == "active" and sub.current_period_end > now
    assert Invoice.objects.filter(subscription=sub, status="paid").count() == 1


def test_process_renewals_expires_canceled_subscription():
    user = UserFactory()
    assign_role(user, "premium")
    now = timezone.now()
    sub = Subscription.objects.create(
        user=user,
        plan=_plan("premium"),
        status="active",
        current_period_end=now - timedelta(days=1),
        cancel_at_period_end=True,
        provider="mock",
    )
    services.process_renewals()
    sub.refresh_from_db()
    assert sub.status == "expired"
    assert "premium" not in user_role_names(user)


# --- webhook ----------------------------------------------------------------


def test_webhook_cancels_subscription(client):
    user = UserFactory()
    sub = services.subscribe(user=user, plan=_plan("premium"))
    assert "premium" in user_role_names(user)
    resp = client.post(
        "/api/v1/billing/webhook/",
        {"type": "subscription.canceled", "subscription_id": sub.provider_subscription_id},
        format="json",
    )
    assert resp.status_code == 200 and resp.json()["data"]["handled"] is True
    sub.refresh_from_db()
    assert sub.status == "canceled"
    assert "premium" not in user_role_names(user)


# --- admin ------------------------------------------------------------------


def test_admin_subscription_list_requires_permission(client):
    plain = UserFactory()
    client.force_authenticate(plain)
    assert client.get("/api/v1/billing/admin/subscriptions/").status_code == 403


def test_admin_subscription_list_ok_for_superuser(client):
    user = UserFactory()
    services.subscribe(user=user, plan=_plan("premium"))
    client.force_authenticate(_superuser())
    data = client.get("/api/v1/billing/admin/subscriptions/").json()["data"]
    assert len(data) >= 1


def test_refund_marks_invoice_refunded(client):
    user = UserFactory()
    services.subscribe(user=user, plan=_plan("premium"))
    invoice = Invoice.objects.get(user=user, status="paid")
    client.force_authenticate(_superuser())
    resp = client.post(f"/api/v1/billing/invoices/{invoice.id}/refund/", {}, format="json")
    assert resp.status_code == 200
    invoice.refresh_from_db()
    assert invoice.status == "refunded"
    # A second refund is rejected.
    assert (
        client.post(f"/api/v1/billing/invoices/{invoice.id}/refund/", {}, format="json").status_code
        == 400
    )


def test_refund_requires_permission(client):
    owner = UserFactory()
    services.subscribe(user=owner, plan=_plan("premium"))
    invoice = Invoice.objects.get(user=owner, status="paid")
    client.force_authenticate(UserFactory())
    assert (
        client.post(f"/api/v1/billing/invoices/{invoice.id}/refund/", {}, format="json").status_code
        == 403
    )
