"""Session/device/login-history recording and revocation."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Device, LoginHistory, UserSession
from common.utils import get_client_ip

if TYPE_CHECKING:
    from django.http import HttpRequest

    from apps.users.models import User

_UA_MAX = 1000


def _user_agent(request: HttpRequest) -> str:
    return request.META.get("HTTP_USER_AGENT", "")[:_UA_MAX]


def _upsert_device(user: User, payload: dict[str, Any] | None) -> Device | None:
    if not payload or not isinstance(payload, dict):
        return None
    platform = payload.get("platform")
    if platform not in Device.Platform.values:
        return None
    push_token = (payload.get("push_token") or "").strip()
    defaults = {
        "device_name": payload.get("device_name", "")[:150],
        "app_version": payload.get("app_version", "")[:30],
        "last_seen_at": timezone.now(),
        "platform": platform,
    }
    if push_token:
        device, _ = Device.objects.update_or_create(
            user=user, push_token=push_token, defaults=defaults
        )
        return device
    return Device.objects.create(user=user, push_token="", **defaults)


def record_login(
    user: User,
    request: HttpRequest,
    refresh: RefreshToken,
    device_payload: dict[str, Any] | None = None,
) -> UserSession:
    device = _upsert_device(user, device_payload)
    exp = refresh.payload.get("exp")
    expires_at = dt.datetime.fromtimestamp(exp, tz=dt.UTC) if exp else None
    session = UserSession.objects.create(
        user=user,
        jti=str(refresh.payload.get("jti", "")),
        device=device,
        ip=get_client_ip(request),
        user_agent=_user_agent(request),
        expires_at=expires_at,
        last_used_at=timezone.now(),
    )
    LoginHistory.objects.create(
        user=user,
        event=LoginHistory.Event.LOGIN,
        ip=get_client_ip(request),
        user_agent=_user_agent(request),
        success=True,
    )
    return session


def record_failed_login(email: str | None, request: HttpRequest) -> None:
    from apps.users.models import User

    user = User.objects.filter(email=(email or "").lower().strip()).first()
    if user is None:
        return
    LoginHistory.objects.create(
        user=user,
        event=LoginHistory.Event.FAILED,
        ip=get_client_ip(request),
        user_agent=_user_agent(request),
        success=False,
    )


def revoke_session(session: UserSession) -> None:
    """Blacklist the session's refresh token and mark it revoked."""
    outstanding = OutstandingToken.objects.filter(jti=session.jti).first()
    if outstanding is not None:
        BlacklistedToken.objects.get_or_create(token=outstanding)
    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at", "updated_at"])
