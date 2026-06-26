"""Custom User model — email is the identifier (no username)."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        PENDING = "pending", "Pending"
        DELETED = "deleted", "Deleted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, null=True, blank=True, unique=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_2fa_enabled = models.BooleanField(default=False)

    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"], name="users_status_idx")]

    def __str__(self) -> str:
        return self.email

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    def soft_delete(self) -> None:
        """Deactivate and mark deleted (GDPR purge runs later, Phase 2)."""
        self.is_active = False
        self.status = self.Status.DELETED
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "status", "deleted_at", "updated_at"])
