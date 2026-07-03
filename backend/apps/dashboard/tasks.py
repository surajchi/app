"""Scheduled task: push a daily market brief to every active user."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger("finpulse")


@shared_task(name="apps.dashboard.tasks.send_daily_brief")
def send_daily_brief() -> int:
    from apps.dashboard.brief import build_brief
    from apps.notifications.services import create_notification
    from apps.users.models import User

    brief = build_brief()
    title = "Your daily market brief"
    body = brief["summary"]

    count = 0
    for user in User.objects.filter(is_active=True).iterator(chunk_size=500):
        create_notification(user=user, type="news", title=title, body=body, data={"brief": True})
        count += 1

    logger.info("dashboard.daily_brief_sent", extra={"count": count})
    return count
