"""Economic calendar routes, mounted at /api/v1/calendar/."""

from __future__ import annotations

from django.urls import path

from apps.econcalendar.views import CalendarListView, CalendarWeekView

urlpatterns = [
    path("", CalendarListView.as_view(), name="calendar-list"),
    path("week/", CalendarWeekView.as_view(), name="calendar-week"),
]
