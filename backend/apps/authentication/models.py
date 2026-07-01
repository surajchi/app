"""Models supporting auth extras: OTP codes, 2FA secrets, OAuth links."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from common.mixins import TimeStampedModel


class OTPCode(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"
        VERIFY = "verify", "Email verification"
        RESET = "reset", "Password reset"
        TWO_FA = "2fa", "Two-factor"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="otp_codes",
    )
    target = models.CharField(max_length=255)  # email or phone
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.EMAIL)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    code_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "otp_codes"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target", "purpose", "-created_at"], name="otp_lookup_idx")]

    def __str__(self) -> str:
        return f"OTP<{self.target}:{self.purpose}>"


class TwoFactor(TimeStampedModel):
    """TOTP secret + recovery codes for a user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="two_factor"
    )
    secret = models.CharField(max_length=64)
    is_enabled = models.BooleanField(default=False)
    recovery_codes = models.JSONField(default=list, blank=True)  # list of hashed codes
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_two_factor"

    def __str__(self) -> str:
        return f"2FA<{self.user_id}:{'on' if self.is_enabled else 'off'}>"


class OAuthAccount(TimeStampedModel):
    class Provider(models.TextChoices):
        GOOGLE = "google", "Google"
        APPLE = "apple", "Apple"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="oauth_accounts"
    )
    provider = models.CharField(max_length=10, choices=Provider.choices)
    provider_uid = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "oauth_accounts"
        constraints = [
            models.UniqueConstraint(fields=["provider", "provider_uid"], name="uniq_provider_uid")
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.provider_uid}"
