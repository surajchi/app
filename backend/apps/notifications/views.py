"""Notification inbox, preferences, device registration, and test send."""

from __future__ import annotations

from django.db.models import QuerySet
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Device
from apps.notifications import services
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.serializers import (
    DeviceRegisterSerializer,
    MarkReadSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
)


@extend_schema(tags=["notifications"])
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Notification]:
        qs = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get("unread") in ("1", "true", "True"):
            qs = qs.filter(read_at__isnull=True)
        return qs.order_by("-created_at")


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MarkReadSerializer

    @extend_schema(tags=["notifications"], request=MarkReadSerializer)
    def post(self, request: Request) -> Response:
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        qs = Notification.objects.filter(user=request.user, read_at__isnull=True)
        if not serializer.validated_data.get("all"):
            qs = qs.filter(id__in=serializer.validated_data.get("ids", []))
        marked = qs.update(read_at=timezone.now())
        return Response({"marked": marked})


@extend_schema(tags=["notifications"])
class PreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> NotificationPreference:
        return services.get_preferences(self.request.user)


class DeviceRegisterView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceRegisterSerializer

    @extend_schema(tags=["notifications"], request=DeviceRegisterSerializer)
    def post(self, request: Request) -> Response:
        serializer = DeviceRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        defaults = {
            "platform": data["platform"],
            "device_name": data["device_name"],
            "app_version": data["app_version"],
            "last_seen_at": timezone.now(),
        }
        push_token = data["push_token"].strip()
        if push_token:
            device, _ = Device.objects.update_or_create(
                user=request.user, push_token=push_token, defaults=defaults
            )
        else:
            device = Device.objects.create(user=request.user, push_token="", **defaults)
        return Response({"id": str(device.id)}, status=status.HTTP_201_CREATED)


class TestNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["notifications"])
    def post(self, request: Request) -> Response:
        notification = services.create_notification(
            user=request.user,
            type="system",
            title="Test notification",
            body="This is a test notification from FinPulse.",
            priority="low",
        )
        return Response(
            {
                "detail": "Test notification sent.",
                "id": str(notification.id) if notification else None,
            },
            status=status.HTTP_201_CREATED,
        )
