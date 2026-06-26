"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.views import LivenessView, ReadinessView

urlpatterns = [
    # Health probes (also used by Docker/Nginx).
    path("healthz/", LivenessView.as_view(), name="healthz"),
    path("readyz/", ReadinessView.as_view(), name="readyz"),
    # Django admin (ops-only; IP-restricted at the edge in prod).
    path("django-admin/", admin.site.urls),
    # OpenAPI schema + Swagger UI.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    # Versioned API.
    path("api/v1/", include("config.api_urls")),
]
