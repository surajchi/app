"""OAuth provider token verification + user upsert (Google, Apple).

Verifiers raise OAuthError on any failure. Live use requires GOOGLE_CLIENT_ID /
APPLE_CLIENT_ID; without them the endpoints return a clear "not configured" error.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

from django.conf import settings
from django.utils import timezone

from apps.authentication.models import OAuthAccount

if TYPE_CHECKING:
    from apps.users.models import User

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"


class OAuthError(Exception):
    """Raised when a provider token is invalid or the provider is misconfigured."""


class OAuthUserInfo(TypedDict):
    provider: str
    uid: str
    email: str
    name: str
    raw: dict[str, Any]


def verify_google_token(id_token_str: str) -> OAuthUserInfo:
    if not settings.GOOGLE_CLIENT_ID:
        raise OAuthError("Google login is not configured.")
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token

        info = google_id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except OAuthError:
        raise
    except Exception as exc:  # noqa: BLE001 - normalize any verification failure
        raise OAuthError("Invalid Google token.") from exc

    return OAuthUserInfo(
        provider=str(OAuthAccount.Provider.GOOGLE),
        uid=str(info["sub"]),
        email=str(info.get("email", "")),
        name=str(info.get("name", "")),
        raw=info,
    )


def verify_apple_token(identity_token: str) -> OAuthUserInfo:
    if not settings.APPLE_CLIENT_ID:
        raise OAuthError("Apple login is not configured.")
    try:
        import jwt

        jwk_client = jwt.PyJWKClient(APPLE_KEYS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(identity_token)
        info = jwt.decode(
            identity_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID,
            issuer=APPLE_ISSUER,
        )
    except OAuthError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise OAuthError("Invalid Apple token.") from exc

    return OAuthUserInfo(
        provider=str(OAuthAccount.Provider.APPLE),
        uid=str(info["sub"]),
        email=str(info.get("email", "")),
        name="",
        raw=info,
    )


def get_or_create_oauth_user(info: OAuthUserInfo) -> User:
    """Find the linked user, link by verified email, or create a new account."""
    from apps.rbac.constants import DEFAULT_ROLE
    from apps.rbac.services import assign_role
    from apps.users.models import User

    account = (
        OAuthAccount.objects.select_related("user")
        .filter(provider=info["provider"], provider_uid=info["uid"])
        .first()
    )
    if account is not None:
        return account.user

    email = (info["email"] or "").lower().strip()
    user = User.objects.filter(email=email).first() if email else None

    if user is None:
        user = User.objects.create_user(
            email=email or f"{info['provider']}_{info['uid']}@oauth.finpulse.local",
            password=None,  # unusable password — OAuth-only account
            full_name=info["name"] or "FinPulse User",
        )
        assign_role(user, DEFAULT_ROLE)

    OAuthAccount.objects.create(
        user=user,
        provider=info["provider"],
        provider_uid=info["uid"],
        email=email,
        raw=info["raw"],
    )

    # A provider-verified email implies the address is confirmed.
    if email and user.email_verified_at is None:
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at", "updated_at"])

    return user
