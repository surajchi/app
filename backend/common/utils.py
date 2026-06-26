"""Small shared helpers."""
from __future__ import annotations

from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str | None:
    """Best-effort client IP, honoring the edge proxy's X-Forwarded-For."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def mask_email(email: str) -> str:
    """Mask an email for safe logging: ``john@x.com`` -> ``j***@x.com``."""
    local, _, domain = email.partition("@")
    if not domain or not local:
        return "***"
    head = local[0]
    return f"{head}***@{domain}"
