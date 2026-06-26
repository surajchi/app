from django.urls import path

from apps.accounts.views import PasswordChangeView, SessionListView, SessionRevokeView
from apps.authentication.views import LoginView, LogoutView, RefreshView, RegisterView

app_name = "authentication"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("sessions/", SessionListView.as_view(), name="sessions"),
    path("sessions/<uuid:id>/", SessionRevokeView.as_view(), name="session-revoke"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
]
