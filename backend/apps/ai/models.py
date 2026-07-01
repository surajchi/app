"""Stored AI predictions (forecasts, technical signals)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from common.mixins import TimeStampedModel


class AIPrediction(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument = models.ForeignKey(
        "markets.Instrument", on_delete=models.CASCADE, related_name="ai_predictions"
    )
    prediction_type = models.CharField(max_length=30)  # price_forecast | technical | ...
    horizon = models.CharField(max_length=10, blank=True)
    value = models.JSONField(default=dict)
    confidence = models.FloatField(default=0.0)
    model = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "ai_predictions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["instrument", "prediction_type", "-created_at"],
                name="ai_pred_lookup_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.instrument_id}:{self.prediction_type}"


class Recommendation(TimeStampedModel):
    class Kind(models.TextChoices):
        BUY_IDEA = "buy_idea", "Buy idea"
        WATCH = "watch", "Watch"
        RISK_WARNING = "risk_warning", "Risk warning"
        DIVERSIFY = "diversify", "Diversify"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations"
    )
    instrument = models.ForeignKey(
        "markets.Instrument", on_delete=models.CASCADE, related_name="recommendations"
    )
    rec_type = models.CharField(max_length=20, choices=Kind.choices)
    score = models.FloatField()
    confidence = models.FloatField(default=0.0)
    rationale = models.TextField(blank=True)
    model = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "recommendations"
        ordering = ["-created_at", "-score"]
        indexes = [models.Index(fields=["user", "-created_at"], name="rec_user_time_idx")]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.instrument_id}:{self.rec_type}"
