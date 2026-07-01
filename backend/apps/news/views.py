"""Public news REST endpoints (read-only)."""

from __future__ import annotations

import logging

from django.conf import settings
from django.db.models import Q, QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.markets.models import Instrument
from apps.news.constants import ArticleStatus
from apps.news.models import NewsArticle, NewsCategory
from apps.news.serializers import (
    NewsCategorySerializer,
    NewsDetailSerializer,
    NewsListSerializer,
)

logger = logging.getLogger("finpulse")

_FEED_BASE = NewsArticle.objects.select_related("category", "sentiment").filter(
    status=ArticleStatus.PUBLISHED
)


@extend_schema(tags=["news"])
class NewsListView(generics.ListAPIView):
    """News feed. Filters: ?category=<slug>&symbol=<SYM>&q=<text>."""

    serializer_class = NewsListSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get_queryset(self) -> QuerySet[NewsArticle]:
        qs = _FEED_BASE
        params = self.request.query_params

        category = params.get("category")
        if category:
            qs = qs.filter(category__slug=category)

        symbol = params.get("symbol")
        if symbol:
            instrument = Instrument.objects.filter(symbol__iexact=symbol).first()
            if instrument is None:
                return qs.none()
            qs = qs.filter(
                entities__linked_kind="instrument", entities__linked_id=instrument.id
            ).distinct()

        query = params.get("q")
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(body__icontains=query))

        return qs.order_by("-published_at")


@extend_schema(tags=["news"])
class NewsDetailView(generics.RetrieveAPIView):
    serializer_class = NewsDetailSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    lookup_field = "id"

    def get_queryset(self) -> QuerySet[NewsArticle]:
        return NewsArticle.objects.select_related("category", "sentiment").prefetch_related(
            "entities"
        )


@extend_schema(tags=["news"])
class NewsTrendingView(generics.ListAPIView):
    """Highest-impact recent articles."""

    serializer_class = NewsListSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    pagination_class = None

    def get_queryset(self) -> QuerySet[NewsArticle]:
        return _FEED_BASE.order_by("-impact_score", "-published_at")[:20]


@extend_schema(tags=["news"])
class NewsSearchView(generics.ListAPIView):
    """Full-text news search. Uses OpenSearch when enabled, else DB search."""

    serializer_class = NewsListSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get_queryset(self):  # type: ignore[override]
        query = self.request.query_params.get("q", "").strip()
        category = self.request.query_params.get("category")

        if getattr(settings, "SEARCH_ENABLED", False):
            try:
                from search.news_index import search_news

                ids = search_news(query, category=category, size=50)
                by_id = {str(a.id): a for a in _FEED_BASE.filter(id__in=ids)}
                return [by_id[i] for i in ids if i in by_id]
            except Exception:  # noqa: BLE001 - degrade to DB search on any outage
                logger.exception("search.query_failed")

        qs = _FEED_BASE
        if category:
            qs = qs.filter(category__slug=category)
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(body__icontains=query))
        return qs.order_by("-published_at")[:50]


@extend_schema(tags=["news"])
class NewsCategoryListView(generics.ListAPIView):
    serializer_class = NewsCategorySerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    pagination_class = None
    queryset = NewsCategory.objects.all()
