"""Watchlist serializers, including live quote enrichment for items."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.markets.models import Instrument
from apps.markets.serializers import InstrumentSerializer
from apps.markets.services import latest_quote
from apps.watchlists.models import Watchlist, WatchlistItem


class WatchlistItemSerializer(serializers.ModelSerializer):
    instrument = InstrumentSerializer(read_only=True)
    instrument_id = serializers.PrimaryKeyRelatedField(
        queryset=Instrument.objects.filter(is_active=True),
        source="instrument",
        write_only=True,
    )
    quote = serializers.SerializerMethodField()

    class Meta:
        model = WatchlistItem
        fields = ["id", "instrument", "instrument_id", "position", "note", "quote", "created_at"]
        read_only_fields = ["id", "position", "created_at"]

    def get_quote(self, obj: WatchlistItem) -> dict[str, Any] | None:
        return latest_quote(obj.instrument)


class WatchlistSerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Watchlist
        fields = ["id", "name", "is_default", "item_count", "created_at"]
        read_only_fields = ["id", "item_count", "created_at"]


class WatchlistDetailSerializer(WatchlistSerializer):
    items = WatchlistItemSerializer(many=True, read_only=True)

    class Meta(WatchlistSerializer.Meta):
        fields = [*WatchlistSerializer.Meta.fields, "items"]


class AddItemSerializer(serializers.Serializer):
    instrument_id = serializers.PrimaryKeyRelatedField(
        queryset=Instrument.objects.filter(is_active=True)
    )
    note = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class ReorderSerializer(serializers.Serializer):
    item_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)
