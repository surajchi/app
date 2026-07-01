"""Billing routes, mounted at /api/v1/billing/."""

from __future__ import annotations

from django.urls import path

from apps.billing.views import (
    AdminSubscriptionListView,
    CancelView,
    InvoiceListView,
    PaymentMethodDefaultView,
    PaymentMethodListCreateView,
    PlanListView,
    RefundView,
    SubscribeView,
    SubscriptionView,
    WebhookView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="billing-plans"),
    path("subscription/", SubscriptionView.as_view(), name="billing-subscription"),
    path("subscribe/", SubscribeView.as_view(), name="billing-subscribe"),
    path("cancel/", CancelView.as_view(), name="billing-cancel"),
    path("invoices/", InvoiceListView.as_view(), name="billing-invoices"),
    path("invoices/<uuid:pk>/refund/", RefundView.as_view(), name="billing-refund"),
    path(
        "payment-methods/",
        PaymentMethodListCreateView.as_view(),
        name="billing-payment-methods",
    ),
    path(
        "payment-methods/<uuid:pk>/default/",
        PaymentMethodDefaultView.as_view(),
        name="billing-payment-method-default",
    ),
    path("webhook/", WebhookView.as_view(), name="billing-webhook"),
    path(
        "admin/subscriptions/",
        AdminSubscriptionListView.as_view(),
        name="billing-admin-subscriptions",
    ),
]
