"""Single composite dashboard endpoint for the app home screen."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.brief import build_brief
from apps.dashboard.services import build_dashboard


@extend_schema(tags=["dashboard"])
class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(build_dashboard(request.user))


@extend_schema(tags=["dashboard"])
class BriefView(APIView):
    """Daily/weekly market brief — shown even when the user has no alerts."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(build_brief())
