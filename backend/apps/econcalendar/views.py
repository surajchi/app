"""Economic calendar read endpoints (public)."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.econcalendar import services
from apps.econcalendar.serializers import EconomicEventSerializer


@extend_schema(tags=["calendar"])
class CalendarListView(generics.ListAPIView):
    """Events in a window. Filters: ?from=&to=&importance=&currency=."""

    serializer_class = EconomicEventSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    pagination_class = None

    def get_queryset(self):  # type: ignore[override]
        params = self.request.query_params
        now = timezone.now()
        start = parse_datetime(params.get("from", "") or "") or now
        end = parse_datetime(params.get("to", "") or "") or (start + timedelta(days=7))
        qs = services.events_between(start, end)
        if importance := params.get("importance"):
            qs = qs.filter(importance=importance)
        if currency := params.get("currency"):
            qs = qs.filter(currency=currency.upper())
        return qs


@extend_schema(tags=["calendar"])
class CalendarWeekView(APIView):
    """This week's events (Mon-Sun), optionally high-impact only (?high=1)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request: Request) -> Response:
        high_only = request.query_params.get("high") in ("1", "true", "True")
        start, end = services.week_bounds()
        events = services.this_week_events(high_only=high_only)
        return Response(
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "events": EconomicEventSerializer(events, many=True).data,
            }
        )
