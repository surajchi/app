"""`/api/v1/` route registry. New feature apps are mounted here per phase."""

from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.authentication.urls")),
    path("users/", include("apps.users.urls")),
    path("profile/", include("apps.profiles.urls")),
    path("markets/", include("apps.markets.urls")),
    path("news/", include("apps.news.urls")),
    # Phase 5+: ai, alerts, ... mounted here.
]
