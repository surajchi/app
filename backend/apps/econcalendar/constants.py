"""Economic calendar enums."""

from __future__ import annotations

from django.db import models


class Importance(models.TextChoices):
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"
