"""Admin audit action codes."""

from __future__ import annotations


class AuditAction:
    USER_UPDATED = "user.updated"
    ROLE_ASSIGNED = "role.assigned"
    ROLE_REMOVED = "role.removed"
    NEWS_MODERATED = "news.moderated"
    BROADCAST_SENT = "broadcast.sent"
