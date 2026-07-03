"""Dashboard route: GET /dashboard/."""

from __future__ import annotations

from django.urls import path

from apps.dashboard.views import BriefView, DashboardView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("brief/", BriefView.as_view(), name="dashboard-brief"),
]
