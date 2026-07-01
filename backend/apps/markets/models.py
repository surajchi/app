"""Market data domain models.

PriceBar is a TimescaleDB hypertable (see migration 0002). Its real primary key
is the composite (instrument_id, interval, ts) created in SQL; ``ts`` is declared
as the Django pk so the ORM has a usable handle (we never look bars up by pk).
"""

from __future__ import annotations

from django.db import models

from apps.markets.constants import AssetClass, Interval
from common.mixins import BaseModel, TimeStampedModel


class Market(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    asset_class = models.CharField(max_length=20, choices=AssetClass.choices)
    region = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "markets"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class Exchange(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    country = models.CharField(max_length=2, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "exchanges"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class Instrument(BaseModel):
    """Unified tradable instrument (per architecture's `instruments` super-type)."""

    asset_class = models.CharField(max_length=20, choices=AssetClass.choices, db_index=True)
    symbol = models.CharField(max_length=32, db_index=True)
    name = models.CharField(max_length=150)
    exchange = models.ForeignKey(
        Exchange, on_delete=models.SET_NULL, null=True, blank=True, related_name="instruments"
    )
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "instruments"
        ordering = ["symbol"]
        constraints = [
            models.UniqueConstraint(
                fields=["asset_class", "symbol", "exchange"], name="uniq_instrument_symbol"
            )
        ]
        indexes = [models.Index(fields=["asset_class", "is_active"], name="instrument_class_idx")]

    def __str__(self) -> str:
        return f"{self.symbol} ({self.asset_class})"


class SymbolAlias(BaseModel):
    """Maps an external provider's symbol to our instrument (anti-corruption)."""

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="aliases")
    provider = models.CharField(max_length=50)
    provider_symbol = models.CharField(max_length=64)

    class Meta:
        db_table = "symbol_aliases"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_symbol"], name="uniq_provider_symbol_alias"
            )
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.provider_symbol}"


class PriceBar(models.Model):
    instrument = models.ForeignKey(
        Instrument, on_delete=models.CASCADE, related_name="bars", db_column="instrument_id"
    )
    interval = models.CharField(max_length=4, choices=Interval.choices)
    # Declared pk for the ORM; the DB primary key is composite (see migration 0002).
    ts = models.DateTimeField(primary_key=True)
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=24, decimal_places=4, null=True, blank=True)
    source = models.CharField(max_length=50, default="synthetic")

    class Meta:
        db_table = "market_price_bars"
        ordering = ["ts"]
        indexes = [
            models.Index(fields=["instrument", "interval", "-ts"], name="pricebar_lookup_idx")
        ]

    def __str__(self) -> str:
        return f"{self.instrument_id} {self.interval} @ {self.ts}"


class DataProviderStatus(TimeStampedModel):
    class Status(models.TextChoices):
        OK = "ok", "OK"
        DEGRADED = "degraded", "Degraded"
        DOWN = "down", "Down"

    provider = models.CharField(max_length=50, unique=True)
    domain = models.CharField(max_length=20, default="market")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OK)
    quota_used = models.PositiveIntegerField(default=0)
    quota_limit = models.PositiveIntegerField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        db_table = "data_provider_status"
        ordering = ["provider"]

    def __str__(self) -> str:
        return f"{self.provider}:{self.status}"
