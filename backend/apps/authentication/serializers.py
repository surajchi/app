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
from apps.users.serializers import UserSerializer  # canonical serializer (includes roles)

__all__ = [
    "UserSerializer",
    "RegisterSerializer",
    "LoginSerializer",
    "RefreshSerializer",
    "LogoutSerializer",
]


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


# --- Phase 2B: verification / reset / OTP / 2FA / OAuth ----------------------


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str) -> str:
        validate_password(value)
        return value


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    device = serializers.DictField(required=False)


class TwoFactorVerifySerializer(serializers.Serializer):
    code = serializers.CharField()


class TwoFactorDisableSerializer(serializers.Serializer):
    code = serializers.CharField()


class TwoFactorLoginSerializer(serializers.Serializer):
    challenge_token = serializers.CharField()
    code = serializers.CharField()
    device = serializers.DictField(required=False)


class OAuthGoogleSerializer(serializers.Serializer):
    id_token = serializers.CharField()
    device = serializers.DictField(required=False)


class OAuthAppleSerializer(serializers.Serializer):
    identity_token = serializers.CharField()
    device = serializers.DictField(required=False)
