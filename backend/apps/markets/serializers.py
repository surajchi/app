from rest_framework import serializers

from apps.markets.models import Exchange, Instrument
from apps.markets.services import latest_quote


class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = ("id", "code", "name", "country", "timezone", "currency", "is_active")
        read_only_fields = fields


class InstrumentSerializer(serializers.ModelSerializer):
    exchange = serializers.SerializerMethodField()
    quote = serializers.SerializerMethodField()

    class Meta:
        model = Instrument
        fields = (
            "id",
            "asset_class",
            "symbol",
            "name",
            "exchange",
            "currency",
            "is_active",
            "quote",
        )
        read_only_fields = fields

    def get_exchange(self, obj: Instrument) -> str | None:
        return obj.exchange.code if obj.exchange_id else None

    def get_quote(self, obj: Instrument) -> dict | None:
        return latest_quote(obj)


class CandleSerializer(serializers.Serializer):
    ts = serializers.DateTimeField()
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    volume = serializers.FloatField(allow_null=True)
