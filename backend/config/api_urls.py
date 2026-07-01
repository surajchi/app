"""`/api/v1/` route registry. New feature apps are mounted here per phase."""

from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.authentication.urls")),
    path("users/", include("apps.users.urls")),
    path("profile/", include("apps.profiles.urls")),
    path("markets/", include("apps.markets.urls")),
    path("news/", include("apps.news.urls")),
    path("ai/", include("apps.ai.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("alerts/", include("apps.alerts.urls")),
    path("watchlists/", include("apps.watchlists.urls")),
    path("portfolios/", include("apps.portfolios.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("admin/", include("apps.administration.urls")),
]
