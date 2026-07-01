"""JWT authentication for WebSocket connections (token via ?token= query param)."""

from __future__ import annotations

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


def get_user_from_token(token: str | None):
    """Resolve a user from a JWT access token, or AnonymousUser if invalid."""
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    from apps.users.models import User

    if not token:
        return AnonymousUser()
    try:
        access = AccessToken(token)
        user_id = access.get("user_id")
    except TokenError:
        return AnonymousUser()

    user = User.objects.filter(id=user_id, is_active=True).first()
    return user or AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Populate scope['user'] from a ?token= access token (anonymous if absent)."""

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        values = query.get("token")
        token = values[0] if values else None
        scope["user"] = await database_sync_to_async(get_user_from_token)(token)
        return await super().__call__(scope, receive, send)
