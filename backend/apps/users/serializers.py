"""Canonical User serializers (shared by auth, users, and admin)."""

from __future__ import annotations

from rest_framework import serializers

from apps.rbac.services import user_role_names
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Public/self representation of a user, including assigned role names."""

    email_verified = serializers.BooleanField(read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "phone",
            "status",
            "is_2fa_enabled",
            "email_verified",
            "is_staff",
            "roles",
            "created_at",
        )
        read_only_fields = fields

    def get_roles(self, obj: User) -> list[str]:
        return user_role_names(obj)


class UserUpdateSerializer(serializers.ModelSerializer):
    """Fields a user may edit on their own account."""

    class Meta:
        model = User
        fields = ("full_name", "phone")

    def validate_phone(self, value: str | None) -> str | None:
        # Normalize empty string to NULL so the unique constraint allows many users
        # without a phone number.
        return value or None
