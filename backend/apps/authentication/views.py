"""Authentication endpoints: register, login, refresh, logout.

Phase 1 covers the JWT foundation. OAuth (Google/Apple), OTP, 2FA, email
verification, password reset, and session/device management arrive in Phase 2.
"""

from __future__ import annotations

import contextlib
import logging

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
from apps.authentication.serializers import (
    LoginSerializer,
    LogoutSerializer,
    RefreshSerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.rbac.constants import DEFAULT_ROLE
from apps.rbac.services import assign_role
from common.utils import get_client_ip, mask_email

logger = logging.getLogger("finpulse")


class RegisterView(generics.CreateAPIView):
    """Create an account and return an initial token pair."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"])
    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Every new account gets the default (free) role.
        assign_role(user, DEFAULT_ROLE)

        refresh = RefreshToken.for_user(user)
        record_login(user, request, refresh, request.data.get("device"))
        logger.info(
            "user.registered",
            extra={"request_id": getattr(request, "request_id", None)},
        )
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "expires_in": int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Email + password -> access/refresh tokens and the user payload."""

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
            # Record the failed attempt and RETURN the error (don't raise) so the
            # audit row commits — a raised exception would roll back the
            # ATOMIC_REQUESTS transaction and lose it.
            record_failed_login(request.data.get("email"), request)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_FAILED",
                        "message": str(exc.detail),
                        "details": None,
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data
        refresh = RefreshToken(data["refresh"])
        record_login(serializer.user, request, refresh, request.data.get("device"))
        return Response(data)


class RefreshView(TokenRefreshView):
    """Exchange a valid refresh token for a new access token (rotation on)."""

    serializer_class = RefreshSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth"

    @extend_schema(tags=["auth"])
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    """Blacklist the supplied refresh token. Idempotent."""

    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["auth"],
        request=LogoutSerializer,
        responses={205: OpenApiResponse(description="Logged out")},
    )
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Already expired/invalid token -> logout is idempotent, treat as success.
        with contextlib.suppress(TokenError):
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)
