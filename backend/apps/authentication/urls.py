from django.urls import path

from apps.accounts.views import PasswordChangeView, SessionListView, SessionRevokeView
from apps.authentication.views import (
    ForgotPasswordView,
    LoginView,
    LogoutView,
    OAuthAppleView,
    OAuthGoogleView,
    OTPRequestView,
    OTPVerifyView,
    RefreshView,
    RegisterView,
    ResendVerificationView,
    ResetPasswordView,
    TwoFactorDisableView,
    TwoFactorLoginView,
    TwoFactorSetupView,
    TwoFactorVerifyView,
    VerifyEmailView,
)

app_name = "authentication"

urlpatterns = [
    # Core (Phase 1)
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Email verification
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
    # Password reset
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    # OTP login
    path("otp/request/", OTPRequestView.as_view(), name="otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="otp-verify"),
    # 2FA (TOTP)
    path("2fa/setup/", TwoFactorSetupView.as_view(), name="2fa-setup"),
    path("2fa/verify/", TwoFactorVerifyView.as_view(), name="2fa-verify"),
    path("2fa/disable/", TwoFactorDisableView.as_view(), name="2fa-disable"),
    path("2fa/login/", TwoFactorLoginView.as_view(), name="2fa-login"),
    # OAuth
    path("oauth/google/", OAuthGoogleView.as_view(), name="oauth-google"),
    path("oauth/apple/", OAuthAppleView.as_view(), name="oauth-apple"),
    # Sessions & password (accounts app)
    path("sessions/", SessionListView.as_view(), name="sessions"),
    path("sessions/<uuid:id>/", SessionRevokeView.as_view(), name="session-revoke"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
]
