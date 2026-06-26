"""Sessions, devices, and login history for account security."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.mixins import TimeStampedModel


class Device(TimeStampedModel):
    class Platform(models.TextChoices):
        IOS = "ios", "iOS"
        ANDROID = "android", "Android"
        WEB = "web", "Web"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices"
    )
    platform = models.CharField(max_length=10, choices=Platform.choices)
    push_token = models.CharField(max_length=255, blank=True)
    device_name = models.CharField(max_length=150, blank=True)
    app_version = models.CharField(max_length=30, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    is_trusted = models.BooleanField(default=False)

    class Meta:
        db_table = "devices"
        ordering = ["-last_seen_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "push_token"],
                condition=~models.Q(push_token=""),
                name="uniq_user_push_token",
            )
        ]

    def __str__(self) -> str:
        return f"{self.platform}:{self.device_name or self.id}"


class LoginHistory(models.Model):
    class Event(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        FAILED = "failed", "Failed login"
        REFRESH = "refresh", "Token refresh"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="login_history"
    )
    event = models.CharField(max_length=20, choices=Event.choices)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "login_history"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"], name="loginhist_user_time_idx")]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.event}"


class UserSession(TimeStampedModel):
    """A refresh-token-backed session (keyed by the token's jti)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions"
    )
    jti = models.CharField(max_length=64, db_index=True)
    device = models.ForeignKey(
        Device, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions"
    )
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_sessions"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "revoked_at"], name="usersession_user_rev_idx")]

    def __str__(self) -> str:
        return f"session<{self.user_id}:{self.jti[:8]}>"

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        return not (self.expires_at is not None and self.expires_at <= timezone.now())
