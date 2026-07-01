"""Portfolio CRUD, transaction ledger, and valuation (user-scoped)."""

from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.portfolios import services
from apps.portfolios.models import Portfolio
from apps.portfolios.serializers import (
    PortfolioSerializer,
    TransactionSerializer,
    ValuationSerializer,
)


@extend_schema(tags=["portfolios"])
class PortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Portfolio]:
        return Portfolio.objects.filter(user=self.request.user)

    def perform_create(self, serializer: BaseSerializer) -> None:
        portfolio = serializer.save(user=self.request.user)
        self._enforce_single_default(portfolio)

    def perform_update(self, serializer: BaseSerializer) -> None:
        portfolio = serializer.save()
        self._enforce_single_default(portfolio)

    def _enforce_single_default(self, portfolio: Portfolio) -> None:
        if portfolio.is_default:
            Portfolio.objects.filter(user=portfolio.user).exclude(pk=portfolio.pk).update(
                is_default=False
            )

    @extend_schema(responses=ValuationSerializer)
    @action(detail=True, methods=["get"])
    def summary(self, request: Request, pk: str | None = None) -> Response:
        portfolio = self.get_object()
        data = services.portfolio_valuation(portfolio)
        return Response(ValuationSerializer(data).data)

    @extend_schema(request=TransactionSerializer, responses=TransactionSerializer)
    @action(detail=True, methods=["get", "post"])
    def transactions(self, request: Request, pk: str | None = None) -> Response:
        portfolio = self.get_object()
        if request.method == "GET":
            qs = portfolio.transactions.select_related("instrument__exchange")
            return Response(TransactionSerializer(qs, many=True).data)

        serializer = TransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            txn = services.apply_transaction(
                portfolio=portfolio,
                instrument=data["instrument"],
                type=data["type"],
                quantity=data["quantity"],
                price=data["price"],
                fee=data.get("fee", 0),
                executed_at=data.get("executed_at"),
                note=data.get("note", ""),
            )
        except services.InsufficientHoldingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)
