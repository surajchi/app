from rest_framework import serializers

from apps.accounts.models import Device
from apps.notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "type", "priority", "title", "body", "data", "read_at", "created_at")
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ("channels", "quiet_hours", "digest", "marketing_opt_in", "updated_at")
        read_only_fields = ("updated_at",)

    def validate_channels(self, value: dict) -> dict:
        if not isinstance(value, dict):
            raise serializers.ValidationError("channels must be an object of type -> [channels].")
        return value


class DeviceRegisterSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=Device.Platform.choices)
    push_token = serializers.CharField(required=False, allow_blank=True, default="")
    device_name = serializers.CharField(required=False, allow_blank=True, default="")
    app_version = serializers.CharField(required=False, allow_blank=True, default="")


class MarkReadSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    all = serializers.BooleanField(required=False, default=False)
