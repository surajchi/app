"""`/api/v1/` route registry. New feature apps are mounted here per phase."""

from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.authentication.urls")),
    path("users/", include("apps.users.urls")),
    path("profile/", include("apps.profiles.urls")),
    # Phase 3+: markets, news, ai, alerts, ... mounted here.
]
