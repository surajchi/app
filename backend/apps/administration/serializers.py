"""Serializers for the admin console API."""

from __future__ import annotations

from rest_framework import serializers

from apps.administration.models import AdminAuditLog
from apps.markets.models import DataProviderStatus
from apps.news.models import NewsArticle
from apps.notifications.constants import Priority
from apps.rbac.models import Role
from apps.rbac.services import user_role_names
from apps.users.models import User


class AdminUserSerializer(serializers.ModelSerializer):
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
            "is_active",
            "is_staff",
            "is_superuser",
            "is_2fa_enabled",
            "email_verified",
            "roles",
            "created_at",
        )
        read_only_fields = fields

    def get_roles(self, obj: User) -> list[str]:
        return user_role_names(obj)


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("status", "is_active", "is_staff")


class RoleAssignSerializer(serializers.Serializer):
    role = serializers.CharField()

    def validate_role(self, value: str) -> str:
        if not Role.objects.filter(name=value).exists():
            raise serializers.ValidationError("Unknown role.")
        return value


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ("id", "name", "description", "is_system", "permissions")
        read_only_fields = fields

    def get_permissions(self, obj: Role) -> list[str]:
        return list(obj.permissions.values_list("code", flat=True))


class AdminNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = (
            "id",
            "title",
            "source",
            "status",
            "is_breaking",
            "impact_score",
            "published_at",
            "created_at",
        )
        read_only_fields = fields


class AdminNewsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = ("status", "is_breaking")


class ProviderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataProviderStatus
        fields = (
            "id",
            "provider",
            "domain",
            "status",
            "quota_used",
            "quota_limit",
            "last_success_at",
            "last_error",
            "updated_at",
        )
        read_only_fields = fields


class BroadcastSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField(allow_blank=True, required=False, default="")
    priority = serializers.ChoiceField(choices=Priority.choices, default=Priority.MEDIUM)
    role = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_role(self, value: str) -> str:
        if value and not Role.objects.filter(name=value).exists():
            raise serializers.ValidationError("Unknown role.")
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = AdminAuditLog
        fields = (
            "id",
            "actor",
            "actor_email",
            "action",
            "target_type",
            "target_id",
            "metadata",
            "ip",
            "created_at",
        )
        read_only_fields = fields
