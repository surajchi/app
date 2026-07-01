"""Portfolio, transaction, and valuation serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.markets.models import Instrument
from apps.markets.serializers import InstrumentSerializer
from apps.portfolios.models import Portfolio, Transaction


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ["id", "name", "base_currency", "is_default", "created_at"]
        read_only_fields = ["id", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    instrument = InstrumentSerializer(read_only=True)
    instrument_id = serializers.PrimaryKeyRelatedField(
        queryset=Instrument.objects.filter(is_active=True),
        source="instrument",
        write_only=True,
    )
    executed_at = serializers.DateTimeField(required=False)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "instrument",
            "instrument_id",
            "type",
            "quantity",
            "price",
            "fee",
            "executed_at",
            "note",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_quantity(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value

    def validate_price(self, value: Decimal) -> Decimal:
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value


# --- Valuation (read-only, computed) ----------------------------------------


class PositionSerializer(serializers.Serializer):
    instrument_id = serializers.CharField()
    symbol = serializers.CharField()
    name = serializers.CharField()
    quantity = serializers.FloatField()
    avg_cost = serializers.FloatField()
    price = serializers.FloatField()
    priced = serializers.BooleanField()
    market_value = serializers.FloatField()
    cost_basis = serializers.FloatField()
    unrealized_pnl = serializers.FloatField()
    unrealized_pct = serializers.FloatField()
    realized_pnl = serializers.FloatField()
    allocation_pct = serializers.FloatField()


class PortfolioTotalsSerializer(serializers.Serializer):
    market_value = serializers.FloatField()
    cost_basis = serializers.FloatField()
    unrealized_pnl = serializers.FloatField()
    unrealized_pct = serializers.FloatField()
    realized_pnl = serializers.FloatField()
    position_count = serializers.IntegerField()


class ValuationSerializer(serializers.Serializer):
    portfolio_id = serializers.CharField()
    name = serializers.CharField()
    base_currency = serializers.CharField()
    positions = PositionSerializer(many=True)
    totals = PortfolioTotalsSerializer()
