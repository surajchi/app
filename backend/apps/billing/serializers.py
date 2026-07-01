"""Billing serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.billing.models import Invoice, PaymentMethod, Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = (
            "id",
            "code",
            "name",
            "description",
            "price_cents",
            "price",
            "currency",
            "interval",
            "trial_days",
            "tier",
            "features",
            "is_active",
        )
        read_only_fields = fields

    def get_price(self, obj: Plan) -> float:
        return round(obj.price_cents / 100, 2)


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "plan",
            "status",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "trial_end",
            "provider",
            "created_at",
        )
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = (
            "id",
            "amount_cents",
            "amount",
            "currency",
            "status",
            "description",
            "period_start",
            "period_end",
            "paid_at",
            "provider_invoice_id",
            "created_at",
        )
        read_only_fields = fields

    def get_amount(self, obj: Invoice) -> float:
        return round(obj.amount_cents / 100, 2)


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = (
            "id",
            "provider",
            "brand",
            "last4",
            "exp_month",
            "exp_year",
            "is_default",
            "created_at",
        )
        read_only_fields = ("id", "provider", "created_at")


class SubscribeSerializer(serializers.Serializer):
    plan = serializers.CharField()
    start_trial = serializers.BooleanField(default=False)

    def validate_plan(self, value: str) -> str:
        if not Plan.objects.filter(code=value, is_active=True).exists():
            raise serializers.ValidationError("Unknown or inactive plan.")
        return value


class CancelSerializer(serializers.Serializer):
    at_period_end = serializers.BooleanField(default=True)


class AddPaymentMethodSerializer(serializers.Serializer):
    brand = serializers.CharField(max_length=30, default="mock")
    last4 = serializers.RegexField(r"^\d{4}$")
    exp_month = serializers.IntegerField(min_value=1, max_value=12)
    exp_year = serializers.IntegerField(min_value=2024, max_value=2100)
    make_default = serializers.BooleanField(default=True)
