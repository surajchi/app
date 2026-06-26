"""Role-Based Access Control: permissions, roles, and user-role assignments."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from common.mixins import TimeStampedModel


class Permission(TimeStampedModel):
    """A fine-grained capability identified by a stable code (e.g. ``news.publish``)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "rbac_permissions"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class Role(TimeStampedModel):
    """A named bundle of permissions assignable to users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False, help_text="System roles cannot be deleted from the admin."
    )
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)

    class Meta:
        db_table = "rbac_roles"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UserRole(models.Model):
    """Assignment of a Role to a User (with audit of who granted it)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_assignments")
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rbac_user_roles"
        unique_together = ("user", "role")
        ordering = ["-granted_at"]

    def __str__(self) -> str:
        return f"{self.user_id} → {self.role_id}"
