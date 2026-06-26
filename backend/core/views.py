"""System endpoints: liveness & readiness probes."""
from __future__ import annotations

from django.core.cache import cache
from django.db import connections
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class LivenessView(APIView):
    """Process is up. No external dependencies checked."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(tags=["system"], responses={200: dict})
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class ReadinessView(APIView):
    """Dependencies (DB, cache) are reachable — safe to receive traffic."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(tags=["system"], responses={200: dict, 503: dict})
    def get(self, request: Request) -> Response:
        checks: dict[str, str] = {}
        healthy = True

        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["database"] = "ok"
        except Exception:  # noqa: BLE001 - report degraded, don't crash the probe
            checks["database"] = "error"
            healthy = False

        try:
            cache.set("readyz:ping", "1", timeout=5)
            checks["cache"] = "ok" if cache.get("readyz:ping") == "1" else "error"
            healthy = healthy and checks["cache"] == "ok"
        except Exception:  # noqa: BLE001
            checks["cache"] = "error"
            healthy = False

        return Response(
            {"status": "ok" if healthy else "degraded", "checks": checks},
            status=200 if healthy else 503,
        )
