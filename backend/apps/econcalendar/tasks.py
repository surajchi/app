"""Scheduled task to keep the economic calendar populated."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger("finpulse")


@shared_task(name="apps.econcalendar.tasks.refresh_calendar")
def refresh_calendar() -> int:
    from apps.econcalendar.services import ensure_events

    created = ensure_events(days=14)
    logger.info("calendar.refreshed", extra={"created": created})
    return created
