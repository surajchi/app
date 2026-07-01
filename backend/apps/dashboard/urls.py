"""Dashboard route: GET /dashboard/."""

from __future__ import annotations

from django.urls import path

from apps.dashboard.views import DashboardView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
]
