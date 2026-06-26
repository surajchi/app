"""`/api/v1/` route registry. New feature apps are mounted here per phase."""
from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.authentication.urls")),
    # Phase 2+: users, profile, markets, news, ai, alerts, ... mounted here.
]
