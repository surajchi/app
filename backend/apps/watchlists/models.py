"""User watchlists and their ordered instrument items."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.markets.models import Instrument
from common.mixins import BaseModel


class Watchlist(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watchlists"
    )
    name = models.CharField(max_length=80)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "watchlists"
        ordering = ["-is_default", "name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="uniq_watchlist_user_name"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.name}"


class WatchlistItem(BaseModel):
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, related_name="items")
    instrument = models.ForeignKey(
        Instrument, on_delete=models.CASCADE, related_name="watchlist_items"
    )
    position = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "watchlist_items"
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["watchlist", "instrument"], name="uniq_watchlist_instrument"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.watchlist_id}:{self.instrument_id}"
