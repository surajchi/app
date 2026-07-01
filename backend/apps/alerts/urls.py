"""Alert routes: /alerts/rules (CRUD via router) + /alerts/history."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.alerts.views import AlertHistoryView, AlertRuleViewSet

router = SimpleRouter()
router.register("rules", AlertRuleViewSet, basename="alert-rule")

urlpatterns = [
    path("history/", AlertHistoryView.as_view(), name="alert-history"),
    path("", include(router.urls)),
]
