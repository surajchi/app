"""Admin console API. Every endpoint is gated by an RBAC permission code.

Superusers implicitly pass all RBAC checks (see apps.rbac.services).
"""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from apps.administration.audit import record_audit
from apps.administration.constants import AuditAction
from apps.administration.models import AdminAuditLog
from apps.administration.serializers import (
    AdminNewsSerializer,
    AdminNewsUpdateSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AuditLogSerializer,
    BroadcastSerializer,
    ProviderStatusSerializer,
    RoleAssignSerializer,
    RoleSerializer,
)
from apps.administration.services import build_overview
from apps.administration.tasks import broadcast_notification
from apps.markets.models import DataProviderStatus
from apps.news.models import NewsArticle
from apps.rbac.models import Role
from apps.rbac.permissions import HasPermission
from apps.rbac.services import assign_role, remove_role, user_role_names
from apps.users.models import User


@extend_schema(tags=["admin"])
class AdminOverviewView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "analytics.view"

    def get(self, request: Request) -> Response:
        return Response(build_overview())


@extend_schema(tags=["admin"])
class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "users.view"
    filter_backends = [SearchFilter]
    search_fields = ["email", "full_name", "phone"]

    def get_queryset(self) -> QuerySet[User]:
        qs = User.objects.all().order_by("-created_at")
        params = self.request.query_params
        if (user_status := params.get("status")) is not None:
            qs = qs.filter(status=user_status)
        if (is_staff := params.get("is_staff")) is not None:
            qs = qs.filter(is_staff=is_staff.lower() in ("1", "true"))
        if (is_active := params.get("is_active")) is not None:
            qs = qs.filter(is_active=is_active.lower() in ("1", "true"))
        return qs


@extend_schema(tags=["admin"])
class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, HasPermission]
    queryset = User.objects.all()

    @property
    def required_permission(self) -> str:
        return "users.manage" if self.request.method in ("PUT", "PATCH") else "users.view"

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.request.method in ("PUT", "PATCH"):
            return AdminUserUpdateSerializer
        return AdminUserSerializer

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        instance = self.get_object()
        partial = bool(kwargs.get("partial", False))
        serializer = AdminUserUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_audit(
            actor=request.user,
            action=AuditAction.USER_UPDATED,
            target_type="user",
            target_id=instance.id,
            metadata={k: str(v) for k, v in serializer.validated_data.items()},
            request=request,
        )
        return Response(AdminUserSerializer(instance).data)


@extend_schema(tags=["admin"])
class AdminUserRolesView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "roles.manage"

    @extend_schema(request=RoleAssignSerializer)
    def post(self, request: Request, user_id: str, role: str | None = None) -> Response:
        target = get_object_or_404(User, id=user_id)
        serializer = RoleAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role_name = serializer.validated_data["role"]
        assign_role(target, role_name, granted_by=request.user)
        record_audit(
            actor=request.user,
            action=AuditAction.ROLE_ASSIGNED,
            target_type="user",
            target_id=target.id,
            metadata={"role": role_name},
            request=request,
        )
        return Response({"roles": user_role_names(target)}, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, user_id: str, role: str | None = None) -> Response:
        target = get_object_or_404(User, id=user_id)
        remove_role(target, role or "")
        record_audit(
            actor=request.user,
            action=AuditAction.ROLE_REMOVED,
            target_type="user",
            target_id=target.id,
            metadata={"role": role},
            request=request,
        )
        return Response({"roles": user_role_names(target)})


@extend_schema(tags=["admin"])
class RoleListView(generics.ListAPIView):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "roles.manage"
    queryset = Role.objects.prefetch_related("permissions").all()


@extend_schema(tags=["admin"])
class AdminNewsListView(generics.ListAPIView):
    serializer_class = AdminNewsSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "news.moderate"
    filter_backends = [SearchFilter]
    search_fields = ["title", "source"]

    def get_queryset(self) -> QuerySet[NewsArticle]:
        qs = NewsArticle.objects.all().order_by("-published_at")
        if (article_status := self.request.query_params.get("status")) is not None:
            qs = qs.filter(status=article_status)
        return qs


@extend_schema(tags=["admin"])
class AdminNewsDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "news.moderate"
    queryset = NewsArticle.objects.all()

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.request.method in ("PUT", "PATCH"):
            return AdminNewsUpdateSerializer
        return AdminNewsSerializer

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        instance = self.get_object()
        partial = bool(kwargs.get("partial", False))
        serializer = AdminNewsUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_audit(
            actor=request.user,
            action=AuditAction.NEWS_MODERATED,
            target_type="news",
            target_id=instance.id,
            metadata={k: str(v) for k, v in serializer.validated_data.items()},
            request=request,
        )
        return Response(AdminNewsSerializer(instance).data)


@extend_schema(tags=["admin"])
class ProviderStatusListView(generics.ListAPIView):
    serializer_class = ProviderStatusSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "analytics.view"
    queryset = DataProviderStatus.objects.all()


@extend_schema(tags=["admin"])
class BroadcastView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "settings.manage"

    @extend_schema(request=BroadcastSerializer)
    def post(self, request: Request) -> Response:
        serializer = BroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        role = data.get("role") or ""

        recipients = User.objects.filter(is_active=True)
        if role:
            recipients = recipients.filter(user_roles__role__name=role).distinct()
        recipient_count = recipients.count()

        broadcast_notification.delay(
            title=data["title"],
            body=data.get("body", ""),
            priority=data["priority"],
            role=role,
        )
        record_audit(
            actor=request.user,
            action=AuditAction.BROADCAST_SENT,
            target_type="broadcast",
            metadata={"title": data["title"], "role": role or "all", "recipients": recipient_count},
            request=request,
        )
        return Response(
            {"detail": "Broadcast queued.", "recipients": recipient_count},
            status=status.HTTP_202_ACCEPTED,
        )


@extend_schema(tags=["admin"])
class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "audit.view"
    queryset = AdminAuditLog.objects.select_related("actor").all()
