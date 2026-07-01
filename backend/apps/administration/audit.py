"""Helpers to record admin actions into the audit log."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from apps.administration.models import AdminAuditLog

if TYPE_CHECKING:
    from rest_framework.request import Request

    from apps.users.models import User


def client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_audit(
    *,
    actor: User | None,
    action: str,
    target_type: str = "",
    target_id: Any = "",
    metadata: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AdminAuditLog:
    return AdminAuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else "",
        metadata=metadata or {},
        ip=client_ip(request),
    )
