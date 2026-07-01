"""Portfolio routes (CRUD + transactions + summary) via a DRF router."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.portfolios.views import PortfolioViewSet

router = SimpleRouter()
router.register("", PortfolioViewSet, basename="portfolio")

urlpatterns = [
    path("", include(router.urls)),
]
