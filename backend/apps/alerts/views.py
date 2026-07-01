"""Alert rule CRUD + fired-alert history (scoped to the authenticated user)."""

from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from apps.alerts.models import Alert, AlertRule
from apps.alerts.serializers import AlertRuleSerializer, AlertSerializer


@extend_schema(tags=["alerts"])
class AlertRuleViewSet(viewsets.ModelViewSet):
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[AlertRule]:
        return AlertRule.objects.filter(user=self.request.user).select_related("instrument")

    def perform_create(self, serializer: BaseSerializer) -> None:
        serializer.save(user=self.request.user)


@extend_schema(tags=["alerts"])
class AlertHistoryView(generics.ListAPIView):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Alert]:
        return Alert.objects.filter(user=self.request.user).select_related("rule")
