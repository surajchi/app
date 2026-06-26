"""User profile & preferences (1:1 with User)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from common.mixins import TimeStampedModel


class Profile(TimeStampedModel):
    class Experience(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        PRO = "pro", "Pro"

    class Risk(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    avatar_url = models.URLField(blank=True)
    # ISO-3166 alpha-2; becomes an FK to countries in Phase 3.
    country = models.CharField(max_length=2, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    base_currency = models.CharField(max_length=3, default="USD")
    language = models.CharField(max_length=5, default="en")
    bio = models.TextField(blank=True)
    experience_level = models.CharField(
        max_length=20, choices=Experience.choices, default=Experience.BEGINNER
    )
    risk_appetite = models.CharField(max_length=10, choices=Risk.choices, default=Risk.MEDIUM)

    class Meta:
        db_table = "profiles"

    def __str__(self) -> str:
        return f"Profile<{self.user_id}>"
