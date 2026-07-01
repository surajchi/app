"""Create notifications, resolve channels from preferences, enqueue delivery."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from django.utils import timezone

from apps.notifications.constants import NotificationType, Priority
from apps.notifications.models import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
)

if TYPE_CHECKING:
    from apps.users.models import User


def get_preferences(user: User) -> NotificationPreference:
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def _in_quiet_hours(prefs: NotificationPreference) -> bool:
    quiet = prefs.quiet_hours or {}
    start, end = quiet.get("start"), quiet.get("end")
    if not start or not end:
        return False
    now = timezone.now().strftime("%H:%M")
    if start <= end:
        return start <= now < end
    return now >= start or now < end  # window wraps midnight


def resolve_channels(
    prefs: NotificationPreference,
    ntype: str,
    priority: str,
    override: Sequence[str] | None,
) -> list[str]:
    channels = (
        list(override) if override is not None else list(prefs.channels.get(ntype, ["in_app"]))
    )
    # During quiet hours, only in-app for non-critical notifications.
    if _in_quiet_hours(prefs) and priority != Priority.CRITICAL:
        channels = [c for c in channels if c == "in_app"] or ["in_app"]
    seen: set[str] = set()
    ordered: list[str] = []
    for channel in channels:
        if channel not in seen:
            seen.add(channel)
            ordered.append(channel)
    return ordered


def create_notification(
    *,
    user: User,
    type: str,
    title: str,
    body: str = "",
    priority: str = "medium",
    data: dict[str, Any] | None = None,
    channels: Sequence[str] | None = None,
    dispatch: bool = True,
) -> Notification | None:
    """Create a notification + queued deliveries and enqueue dispatch.

    Returns None if suppressed (e.g. marketing without opt-in).
    """
    prefs = get_preferences(user)
    if type == NotificationType.MARKETING and not prefs.marketing_opt_in:
        return None

    resolved = resolve_channels(prefs, type, priority, channels)
    notification = Notification.objects.create(
        user=user, type=type, priority=priority, title=title, body=body, data=data or {}
    )
    NotificationDelivery.objects.bulk_create(
        [NotificationDelivery(notification=notification, channel=c) for c in resolved]
    )

    if dispatch:
        from apps.notifications.tasks import dispatch_notification

        dispatch_notification.delay(str(notification.id))
    return notification
