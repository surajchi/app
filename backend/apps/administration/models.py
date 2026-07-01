"""Immutable audit trail of privileged admin actions."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from common.mixins import TimeStampedModel


class AdminAuditLog(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "admin_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "-created_at"], name="audit_actor_time_idx"),
            models.Index(fields=["action", "-created_at"], name="audit_action_time_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.action}:{self.target_type}:{self.target_id}"
