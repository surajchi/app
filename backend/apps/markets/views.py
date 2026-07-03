"""Public market-data REST endpoints (read-only)."""

from __future__ import annotations

from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.markets import services
from apps.markets.constants import DEFAULT_HISTORY_INTERVAL, VALID_INTERVALS
from apps.markets.models import Exchange, Instrument
from apps.markets.serializers import (
    CandleSerializer,
    ExchangeSerializer,
    InstrumentSerializer,
)


def _get_instrument(symbol: str) -> Instrument:
    instrument = (
        Instrument.objects.select_related("exchange")
        .filter(symbol__iexact=symbol, is_active=True)
        .first()
    )
    if instrument is None:
        raise NotFound("Instrument not found.")
    return instrument


@extend_schema(tags=["markets"])
class ExchangeListView(generics.ListAPIView):
    serializer_class = ExchangeSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    queryset = Exchange.objects.filter(is_active=True)


@extend_schema(tags=["markets"])
class InstrumentListView(generics.ListAPIView):
    serializer_class = InstrumentSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    filter_backends = [SearchFilter]
    search_fields = ["symbol", "name"]
    filterset_fields = ["asset_class"]

    def get_queryset(self):  # type: ignore[override]
        qs = Instrument.objects.select_related("exchange").filter(is_active=True)
        asset_class = self.request.query_params.get("asset_class")
        if asset_class:
            qs = qs.filter(asset_class=asset_class)
        exchange = self.request.query_params.get("exchange")
        if exchange:
            qs = qs.filter(exchange__code__iexact=exchange)
        return qs


@extend_schema(tags=["markets"])
class InstrumentDetailView(generics.RetrieveAPIView):
    serializer_class = InstrumentSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get_object(self) -> Instrument:
        return _get_instrument(self.kwargs["symbol"])


class QuoteView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(tags=["markets"])
    def get(self, request: Request, symbol: str) -> Response:
        instrument = _get_instrument(symbol)
        quote = services.latest_quote(instrument)
        if quote is None:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_QUOTE",
                        "message": "No quote available yet.",
                        "details": None,
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"symbol": instrument.symbol, **quote})


class HistoryView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(tags=["markets"])
    def get(self, request: Request, symbol: str) -> Response:
        instrument = _get_instrument(symbol)
        interval = request.query_params.get("interval", DEFAULT_HISTORY_INTERVAL)
        if interval not in VALID_INTERVALS:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_INTERVAL",
                        "message": f"interval must be one of {sorted(VALID_INTERVALS)}.",
                        "details": None,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        start = parse_datetime(request.query_params.get("from", "") or "")
        end = parse_datetime(request.query_params.get("to", "") or "")
        bars = services.history(instrument, interval, start=start, end=end)
        return Response(
            {
                "symbol": instrument.symbol,
                "interval": interval,
                "candles": CandleSerializer(bars, many=True).data,
            }
        )


class MoversView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(tags=["markets"])
    def get(self, request: Request) -> Response:
        kind = request.query_params.get("type", "gainers")
        asset_class = request.query_params.get("asset_class")
        try:
            limit = min(int(request.query_params.get("limit", 10)), 50)
        except ValueError:
            limit = 10
        rows = services.movers(asset_class=asset_class, kind=kind, limit=limit)
        data = [
            {
                "symbol": row["instrument"].symbol,
                "name": row["instrument"].name,
                "asset_class": row["instrument"].asset_class,
                "price": row["quote"].get("price"),
                "change": row["quote"].get("change"),
                "change_percent": row["quote"].get("change_percent"),
            }
            for row in rows
        ]
        return Response({"type": kind, "results": data})


class InstrumentAnalysisView(APIView):
    """Fused AI analysis: quote + history + forecast + technical + news effects."""

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["markets"])
    def get(self, request: Request, symbol: str) -> Response:
        from apps.markets.analysis import build_instrument_analysis

        instrument = _get_instrument(symbol)
        try:
            horizon = int(request.query_params.get("horizon", 7))
        except ValueError:
            horizon = 7
        horizon = max(1, min(horizon, 30))
        return Response(build_instrument_analysis(instrument, horizon=horizon))
