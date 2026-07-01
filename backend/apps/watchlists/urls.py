"""Watchlist routes (CRUD + item actions) via a DRF router."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.watchlists.views import WatchlistViewSet

router = SimpleRouter()
router.register("", WatchlistViewSet, basename="watchlist")

urlpatterns = [
    path("", include(router.urls)),
]
