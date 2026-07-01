"""Async admin operations (broadcast announcements to users)."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger("finpulse")


@shared_task(name="apps.administration.tasks.broadcast_notification")
def broadcast_notification(
    *, title: str, body: str = "", priority: str = "medium", role: str = ""
) -> int:
    """Create a system notification for every active user (optionally by role)."""
    from apps.notifications.services import create_notification
    from apps.users.models import User

    users = User.objects.filter(is_active=True)
    if role:
        users = users.filter(user_roles__role__name=role).distinct()

    count = 0
    for user in users.iterator(chunk_size=500):
        create_notification(user=user, type="system", title=title, body=body, priority=priority)
        count += 1

    logger.info("admin.broadcast_sent", extra={"count": count, "role": role or "all"})
    return count
