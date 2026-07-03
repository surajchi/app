"""Economic calendar events (macro releases: CPI, NFP, rate decisions, …)."""

from __future__ import annotations

from django.db import models

from apps.econcalendar.constants import Importance
from common.mixins import BaseModel


class EconomicEvent(BaseModel):
    title = models.CharField(max_length=120)
    country = models.CharField(max_length=2, blank=True)
    currency = models.CharField(max_length=3, db_index=True)
    importance = models.CharField(
        max_length=8, choices=Importance.choices, default=Importance.MEDIUM
    )
    category = models.CharField(max_length=30, blank=True)
    event_time = models.DateTimeField(db_index=True)
    actual = models.CharField(max_length=20, blank=True)
    forecast = models.CharField(max_length=20, blank=True)
    previous = models.CharField(max_length=20, blank=True)
    unit = models.CharField(max_length=10, blank=True)
    source = models.CharField(max_length=30, default="generated")

    class Meta:
        db_table = "economic_events"
        ordering = ["event_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["currency", "title", "event_time"], name="uniq_econ_event"
            ),
        ]
        indexes = [
            models.Index(fields=["event_time", "importance"], name="econ_time_imp_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.currency}:{self.title}@{self.event_time:%Y-%m-%d}"
