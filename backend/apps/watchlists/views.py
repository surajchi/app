"""Watchlist CRUD plus item add/remove/reorder actions (user-scoped)."""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import Max, QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.watchlists.models import Watchlist, WatchlistItem
from apps.watchlists.serializers import (
    AddItemSerializer,
    ReorderSerializer,
    WatchlistDetailSerializer,
    WatchlistItemSerializer,
    WatchlistSerializer,
)


@extend_schema(tags=["watchlists"])
class WatchlistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Watchlist]:
        return Watchlist.objects.filter(user=self.request.user).prefetch_related(
            "items__instrument__exchange"
        )

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action in {"retrieve", "create", "update", "partial_update"}:
            return WatchlistDetailSerializer
        return WatchlistSerializer

    def perform_create(self, serializer: BaseSerializer) -> None:
        watchlist = serializer.save(user=self.request.user)
        self._enforce_single_default(watchlist)

    def perform_update(self, serializer: BaseSerializer) -> None:
        watchlist = serializer.save()
        self._enforce_single_default(watchlist)

    def _enforce_single_default(self, watchlist: Watchlist) -> None:
        if watchlist.is_default:
            Watchlist.objects.filter(user=watchlist.user).exclude(pk=watchlist.pk).update(
                is_default=False
            )

    @extend_schema(request=AddItemSerializer, responses=WatchlistItemSerializer)
    @action(detail=True, methods=["post"])
    def items(self, request: Request, pk: str | None = None) -> Response:
        watchlist = self.get_object()
        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instrument = serializer.validated_data["instrument_id"]
        next_pos = (watchlist.items.aggregate(m=Max("position")).get("m") or 0) + 1
        try:
            item = WatchlistItem.objects.create(
                watchlist=watchlist,
                instrument=instrument,
                note=serializer.validated_data.get("note", ""),
                position=next_pos,
            )
        except IntegrityError:
            return Response(
                {"detail": "Instrument already in this watchlist."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(WatchlistItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path="items/(?P<item_id>[^/.]+)")
    def remove_item(
        self, request: Request, pk: str | None = None, item_id: str | None = None
    ) -> Response:
        watchlist = self.get_object()
        deleted, _ = WatchlistItem.all_objects.filter(watchlist=watchlist, id=item_id).delete()
        if not deleted:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=ReorderSerializer)
    @action(detail=True, methods=["post"])
    def reorder(self, request: Request, pk: str | None = None) -> Response:
        watchlist = self.get_object()
        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = [str(i) for i in serializer.validated_data["item_ids"]]
        existing = {str(i.id): i for i in watchlist.items.all()}
        with transaction.atomic():
            for position, item_id in enumerate(ids, start=1):
                item = existing.get(item_id)
                if item is not None:
                    item.position = position
                    item.save(update_fields=["position", "updated_at"])
        return Response(WatchlistDetailSerializer(watchlist).data)
