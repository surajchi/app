"""Serializers for registration, login, token refresh, and logout."""
from __future__ import annotations

from typing import Any

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings

from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Public representation of a user (read-only)."""

    email_verified = serializers.BooleanField(read_only=True)

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
            "created_at",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
        min_length=8,
    )

    class Meta:
        model = User
        fields = ("email", "full_name", "password")

    def validate_email(self, value: str) -> str:
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """Email/password login returning a token pair plus the user payload."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # Emails are stored lowercased at signup; normalize the input so login
        # is case-insensitive on the email.
        if attrs.get(self.username_field):
            attrs[self.username_field] = attrs[self.username_field].lower().strip()
        data = super().validate(attrs)
        return {
            "access": data["access"],
            "refresh": data["refresh"],
            "expires_in": int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
            "user": UserSerializer(self.user).data,
        }


class RefreshSerializer(TokenRefreshSerializer):
    """Adds `expires_in` to the standard refresh response."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        data = super().validate(attrs)
        data["expires_in"] = int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
