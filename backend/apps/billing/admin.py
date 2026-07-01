"""Admin registrations for billing models."""

from __future__ import annotations

from django.contrib import admin

from apps.billing.models import Invoice, PaymentMethod, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "price_cents", "currency", "interval", "tier", "is_active")
    list_filter = ("is_active", "interval")
    search_fields = ("code", "name")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "current_period_end", "cancel_at_period_end")
    list_filter = ("status", "plan")
    search_fields = ("user__email", "provider_subscription_id")
    autocomplete_fields = ("user", "plan")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_cents", "currency", "status", "paid_at", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("user__email", "provider_invoice_id")


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("user", "brand", "last4", "is_default")
    list_filter = ("brand", "is_default")
    search_fields = ("user__email",)
