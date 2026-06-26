"""Endpoints for sessions, devices, activity, and password change."""

from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Device, LoginHistory, UserSession
from apps.accounts.serializers import (
    DeviceSerializer,
    LoginHistorySerializer,
    PasswordChangeSerializer,
    UserSessionSerializer,
)
from apps.accounts.services import revoke_session


@extend_schema(tags=["account"])
class SessionListView(generics.ListAPIView):
    """List the authenticated user's active (non-revoked) sessions."""

    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[UserSession]:
        return (
            UserSession.objects.filter(user=self.request.user, revoked_at__isnull=True)
            .select_related("device")
            .order_by("-created_at")
        )


@extend_schema(tags=["account"])
class SessionRevokeView(generics.DestroyAPIView):
    """Revoke a session (blacklists its refresh token)."""

    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self) -> QuerySet[UserSession]:
        return UserSession.objects.filter(user=self.request.user, revoked_at__isnull=True)

    def perform_destroy(self, instance: UserSession) -> None:
        revoke_session(instance)


@extend_schema(tags=["account"])
class DeviceListView(generics.ListAPIView):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Device]:
        return Device.objects.filter(user=self.request.user).order_by("-last_seen_at")


@extend_schema(tags=["account"])
class DeviceDeleteView(generics.DestroyAPIView):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self) -> QuerySet[Device]:
        return Device.objects.filter(user=self.request.user)


@extend_schema(tags=["account"])
class ActivityView(generics.ListAPIView):
    """The authenticated user's login history."""

    serializer_class = LoginHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[LoginHistory]:
        return LoginHistory.objects.filter(user=self.request.user).order_by("-created_at")


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    @extend_schema(
        tags=["account"],
        request=PasswordChangeSerializer,
        responses={200: OpenApiResponse(description="Password changed")},
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
