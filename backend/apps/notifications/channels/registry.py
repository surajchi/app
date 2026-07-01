"""Resolve enabled channels. Unconfigured channels (push/telegram/sms) return
None so deliveries are marked SKIPPED rather than failing — activate them later
by adding an implementation + keys."""

from __future__ import annotations

from apps.notifications.channels.base import NotificationChannel
from apps.notifications.channels.email import EmailChannel
from apps.notifications.channels.in_app import InAppChannel

_CHANNELS: dict[str, type] = {
    "in_app": InAppChannel,
    "email": EmailChannel,
}


def get_channel(name: str) -> NotificationChannel | None:
    channel_cls = _CHANNELS.get(name)
    return channel_cls() if channel_cls else None
