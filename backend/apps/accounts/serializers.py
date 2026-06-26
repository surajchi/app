from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import Device, LoginHistory, UserSession


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = (
            "id",
            "platform",
            "device_name",
            "app_version",
            "is_trusted",
            "last_seen_at",
            "created_at",
        )
        read_only_fields = fields


class DeviceBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ("id", "platform", "device_name")
        read_only_fields = fields


class UserSessionSerializer(serializers.ModelSerializer):
    device = DeviceBriefSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSession
        fields = (
            "id",
            "ip",
            "user_agent",
            "device",
            "is_active",
            "last_used_at",
            "expires_at",
            "created_at",
        )
        read_only_fields = fields


class LoginHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginHistory
        fields = ("id", "event", "ip", "user_agent", "success", "created_at")
        read_only_fields = fields


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value: str) -> str:
        validate_password(value, self.context["request"].user)
        return value
