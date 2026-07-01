"""Authentication endpoints.

Phase 1: register, login, refresh, logout (JWT foundation).
Phase 2B: email verification, password reset, OTP login, 2FA (TOTP), OAuth.
"""

from __future__ import annotations

import contextlib
import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.services import record_failed_login, record_login
from apps.authentication import emails, oauth, otp, tokens, totp
from apps.authentication.models import OTPCode, TwoFactor
from apps.authentication.serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    OAuthAppleSerializer,
    OAuthGoogleSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    RefreshSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    TwoFactorDisableSerializer,
    TwoFactorLoginSerializer,
    TwoFactorVerifySerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from apps.rbac.constants import DEFAULT_ROLE
from apps.rbac.services import assign_role
from apps.users.models import User
from common.utils import get_client_ip, mask_email

logger = logging.getLogger("finpulse")


# --- helpers ----------------------------------------------------------------


def _error(
    message: str, code: str = "ERROR", http_status: int = status.HTTP_400_BAD_REQUEST
) -> Response:
    """Return a pre-shaped error envelope (so DB writes before it still commit)."""
    return Response(
        {"success": False, "error": {"code": code, "message": message, "details": None}},
        status=http_status,
    )


def _token_payload(user: User, request: Request, device_payload: dict | None = None) -> dict:
    """Issue a fresh token pair, record the session, and build the auth payload."""
    refresh = RefreshToken.for_user(user)
    record_login(user, request, refresh, device_payload)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "expires_in": int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
        "user": UserSerializer(user).data,
    }


def _send_verification(user: User) -> None:
    try:
        emails.send_verification_email(user, tokens.make_email_verification_token(user))
    except Exception:  # noqa: BLE001 - email failure must not break the flow
        logger.exception("email.verification_send_failed")


# --- core (Phase 1) ---------------------------------------------------------


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"])
    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        assign_role(user, DEFAULT_ROLE)
        _send_verification(user)
        logger.info("user.registered", extra={"request_id": getattr(request, "request_id", None)})
        payload = _token_payload(user, request, request.data.get("device"))
        return Response(payload, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """Email + password. Returns a 2FA challenge instead of tokens if 2FA is on."""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"])
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        logger.info(
            "user.login_attempt",
            extra={
                "request_id": getattr(request, "request_id", None),
                "email": mask_email(str(request.data.get("email", ""))),
                "ip": get_client_ip(request),
            },
        )
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as exc:
            record_failed_login(request.data.get("email"), request)
            return _error(str(exc.detail), "AUTHENTICATION_FAILED", status.HTTP_401_UNAUTHORIZED)

        user = serializer.user
        if user.is_2fa_enabled:
            return Response(
                {"challenge": "2fa", "challenge_token": tokens.make_2fa_challenge_token(user)}
            )

        data = serializer.validated_data
        record_login(user, request, RefreshToken(data["refresh"]), request.data.get("device"))
        return Response(data)


class RefreshView(TokenRefreshView):
    serializer_class = RefreshSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"])
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["auth"], request=LogoutSerializer, responses={205: OpenApiResponse()})
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with contextlib.suppress(TokenError):
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)


# --- email verification -----------------------------------------------------


class VerifyEmailView(APIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"], request=VerifyEmailSerializer, responses={200: OpenApiResponse()})
    def post(self, request: Request) -> Response:
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = tokens.read_email_verification_token(
                serializer.validated_data["token"], settings.EMAIL_VERIFICATION_TTL
            )
        except signing.BadSignature:
            return _error("Invalid or expired verification link.", "INVALID_TOKEN")

        user = User.objects.filter(id=data.get("uid")).first()
        if user is None:
            return _error("Invalid verification link.", "INVALID_TOKEN")
        if user.email_verified_at is None:
            user.email_verified_at = timezone.now()
            user.save(update_fields=["email_verified_at", "updated_at"])
        return Response({"detail": "Email verified."})


class ResendVerificationView(APIView):
    serializer_class = ResendVerificationSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"], request=ResendVerificationSerializer)
    def post(self, request: Request) -> Response:
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"].lower()).first()
        if user is not None and user.email_verified_at is None:
            _send_verification(user)
        return Response({"detail": "If applicable, a verification email has been sent."})


# --- password reset ---------------------------------------------------------


class ForgotPasswordView(APIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"], request=ForgotPasswordSerializer)
    def post(self, request: Request) -> Response:
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"].lower()).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
            token = default_token_generator.make_token(user)
            with contextlib.suppress(Exception):
                emails.send_password_reset_email(user, uid, token)
        # Never reveal whether the account exists.
        return Response({"detail": "If an account exists, a reset link has been sent."})


class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"], request=ResetPasswordSerializer)
    def post(self, request: Request) -> Response:
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = urlsafe_base64_decode(serializer.validated_data["uid"]).decode()
            user = User.objects.get(pk=uid)
        except (ValueError, User.DoesNotExist):
            return _error("Invalid reset link.", "INVALID_TOKEN")

        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return _error("Invalid or expired reset link.", "INVALID_TOKEN")

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "Password has been reset."})


# --- OTP login --------------------------------------------------------------


class OTPRequestView(APIView):
    serializer_class = OTPRequestSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"], request=OTPRequestSerializer)
    def post(self, request: Request) -> Response:
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        user = User.objects.filter(email=email, is_active=True).first()
        if user is not None:
            code = otp.issue_otp(email, str(OTPCode.Purpose.LOGIN), user=user)
            with contextlib.suppress(Exception):
                emails.send_otp_email(email, code)
        return Response({"detail": "If an account exists, a code has been sent."})


class OTPVerifyView(APIView):
    serializer_class = OTPVerifySerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"], request=OTPVerifySerializer)
    def post(self, request: Request) -> Response:
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        verified = otp.verify_otp(
            email, str(OTPCode.Purpose.LOGIN), serializer.validated_data["code"]
        )
        if verified is None:
            return _error("Invalid or expired code.", "INVALID_OTP", status.HTTP_400_BAD_REQUEST)

        user = verified.user or User.objects.filter(email=email, is_active=True).first()
        if user is None or not user.is_active:
            return _error(
                "Account unavailable.", "AUTHENTICATION_FAILED", status.HTTP_401_UNAUTHORIZED
            )
        return Response(_token_payload(user, request, serializer.validated_data.get("device")))


# --- 2FA (TOTP) -------------------------------------------------------------


class TwoFactorSetupView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["auth"], responses={200: OpenApiResponse()})
    def post(self, request: Request) -> Response:
        secret = totp.generate_secret()
        TwoFactor.objects.update_or_create(
            user=request.user, defaults={"secret": secret, "is_enabled": False}
        )
        return Response(
            {"secret": secret, "otpauth_url": totp.provisioning_uri(secret, request.user.email)}
        )


class TwoFactorVerifyView(APIView):
    serializer_class = TwoFactorVerifySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["auth"], request=TwoFactorVerifySerializer)
    def post(self, request: Request) -> Response:
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tf = TwoFactor.objects.filter(user=request.user).first()
        if tf is None:
            return _error("Start 2FA setup first.", "TWO_FA_NOT_SETUP")
        if not totp.verify_totp(tf.secret, serializer.validated_data["code"]):
            return _error("Invalid authentication code.", "INVALID_2FA")

        recovery = totp.generate_recovery_codes()
        tf.is_enabled = True
        tf.confirmed_at = timezone.now()
        tf.recovery_codes = totp.hash_recovery_codes(recovery)
        tf.save(update_fields=["is_enabled", "confirmed_at", "recovery_codes", "updated_at"])
        request.user.is_2fa_enabled = True
        request.user.save(update_fields=["is_2fa_enabled", "updated_at"])
        # Recovery codes are returned once, in plaintext.
        return Response(
            {"detail": "Two-factor authentication enabled.", "recovery_codes": recovery}
        )


class TwoFactorDisableView(APIView):
    serializer_class = TwoFactorDisableSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["auth"], request=TwoFactorDisableSerializer)
    def post(self, request: Request) -> Response:
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tf = TwoFactor.objects.filter(user=request.user, is_enabled=True).first()
        if tf is None:
            return _error("Two-factor is not enabled.", "TWO_FA_NOT_ENABLED")

        code = serializer.validated_data["code"]
        if (
            not totp.verify_totp(tf.secret, code)
            and totp.consume_recovery_code(code, tf.recovery_codes) is None
        ):
            return _error("Invalid authentication code.", "INVALID_2FA")

        tf.is_enabled = False
        tf.recovery_codes = []
        tf.save(update_fields=["is_enabled", "recovery_codes", "updated_at"])
        request.user.is_2fa_enabled = False
        request.user.save(update_fields=["is_2fa_enabled", "updated_at"])
        return Response({"detail": "Two-factor authentication disabled."})


class TwoFactorLoginView(APIView):
    """Complete a login that returned a 2FA challenge."""

    serializer_class = TwoFactorLoginSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"], request=TwoFactorLoginSerializer)
    def post(self, request: Request) -> Response:
        serializer = TwoFactorLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = tokens.read_2fa_challenge_token(
                serializer.validated_data["challenge_token"], settings.TWO_FA_CHALLENGE_TTL
            )
        except signing.BadSignature:
            return _error(
                "Invalid or expired challenge.", "INVALID_CHALLENGE", status.HTTP_401_UNAUTHORIZED
            )

        user = User.objects.filter(id=data.get("uid"), is_active=True).first()
        tf = TwoFactor.objects.filter(user=user, is_enabled=True).first() if user else None
        if user is None or tf is None:
            return _error("Invalid challenge.", "INVALID_CHALLENGE", status.HTTP_401_UNAUTHORIZED)

        code = serializer.validated_data["code"]
        if totp.verify_totp(tf.secret, code):
            authenticated = True
        else:
            remaining = totp.consume_recovery_code(code, tf.recovery_codes)
            authenticated = remaining is not None
            if authenticated:
                tf.recovery_codes = remaining
                tf.save(update_fields=["recovery_codes", "updated_at"])

        if not authenticated:
            return _error("Invalid 2FA code.", "INVALID_2FA", status.HTTP_401_UNAUTHORIZED)
        return Response(_token_payload(user, request, serializer.validated_data.get("device")))


# --- OAuth ------------------------------------------------------------------


class _OAuthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    def _complete(
        self, info: oauth.OAuthUserInfo, request: Request, device: dict | None
    ) -> Response:
        user = oauth.get_or_create_oauth_user(info)
        if not user.is_active:
            return _error(
                "Account unavailable.", "AUTHENTICATION_FAILED", status.HTTP_401_UNAUTHORIZED
            )
        return Response(_token_payload(user, request, device))


class OAuthGoogleView(_OAuthView):
    serializer_class = OAuthGoogleSerializer

    @extend_schema(tags=["auth"], request=OAuthGoogleSerializer)
    def post(self, request: Request) -> Response:
        serializer = OAuthGoogleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            info = oauth.verify_google_token(serializer.validated_data["id_token"])
        except oauth.OAuthError as exc:
            return _error(str(exc), "OAUTH_ERROR")
        return self._complete(info, request, serializer.validated_data.get("device"))


class OAuthAppleView(_OAuthView):
    serializer_class = OAuthAppleSerializer

    @extend_schema(tags=["auth"], request=OAuthAppleSerializer)
    def post(self, request: Request) -> Response:
        serializer = OAuthAppleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            info = oauth.verify_apple_token(serializer.validated_data["identity_token"])
        except oauth.OAuthError as exc:
            return _error(str(exc), "OAUTH_ERROR")
        return self._complete(info, request, serializer.validated_data.get("device"))
