"""Service-to-service auth dependency."""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.config import settings


async def require_service_token(x_service_token: str | None = Header(default=None)) -> None:
    if settings.token and x_service_token != settings.token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token"
        )
