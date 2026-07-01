"""In-app delivery over the realtime WebSocket gateway (free, no keys)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.notifications.channels.base import SendResult

if TYPE_CHECKING:
    from apps.notifications.models import Notification, NotificationDelivery


class InAppChannel:
    name = "in_app"

    def send(self, notification: Notification, delivery: NotificationDelivery) -> SendResult:
        from realtime.publish import publish_notification

        publish_notification(
            str(notification.user_id),
            {
                "id": str(notification.id),
                "type": notification.type,
                "priority": notification.priority,
                "title": notification.title,
                "body": notification.body,
                "data": notification.data,
                "created_at": notification.created_at.isoformat(),
            },
        )
        return SendResult(ok=True, provider_id="ws")
