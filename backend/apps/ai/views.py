"""AI endpoints — thin proxies to the FastAPI AI service (auth required)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai import recommendations, services
from apps.ai.client import AIServiceError
from apps.markets.models import Instrument

MODEL_CATALOG = [
    {"name": "forecast", "model": "linreg-v1", "task": "price_forecast", "engine": "scikit-learn"},
    {"name": "technical", "model": "ta-v1", "task": "technical", "engine": "pandas"},
    {"name": "sentiment", "model": "lexicon-v1", "task": "sentiment", "engine": "lexicon"},
    {
        "name": "recommendations",
        "model": "rec-blend-v1",
        "task": "recommendation",
        "engine": "heuristic",
    },
]


def _instrument(symbol: str) -> Instrument:
    instrument = Instrument.objects.filter(symbol__iexact=symbol, is_active=True).first()
    if instrument is None:
        raise NotFound("Instrument not found.")
    return instrument


def _unavailable() -> Response:
    return Response(
        {
            "success": False,
            "error": {
                "code": "AI_UNAVAILABLE",
                "message": "The AI service is temporarily unavailable.",
                "details": None,
            },
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class ForecastView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["ai"])
    def get(self, request: Request, symbol: str) -> Response:
        instrument = _instrument(symbol)
        try:
            horizon = int(request.query_params.get("horizon", 7))
        except ValueError:
            horizon = 7
        horizon = max(1, min(horizon, 30))
        try:
            return Response(services.get_forecast(instrument, horizon))
        except AIServiceError:
            return _unavailable()


class TechnicalView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["ai"])
    def get(self, request: Request, symbol: str) -> Response:
        instrument = _instrument(symbol)
        try:
            return Response(services.get_technical(instrument))
        except AIServiceError:
            return _unavailable()


class RecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["ai"])
    def get(self, request: Request) -> Response:
        try:
            limit = min(int(request.query_params.get("limit", 10)), 50)
        except ValueError:
            limit = 10
        return Response(recommendations.generate(request.user, limit))


class ModelsView(APIView):
    """Catalog of AI models currently served (lightweight registry surface)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(tags=["ai"])
    def get(self, request: Request) -> Response:
        return Response({"models": MODEL_CATALOG})
