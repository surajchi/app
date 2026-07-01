"""Email delivery (console backend in dev; SMTP in prod). Free — no keys in dev."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail

from apps.notifications.channels.base import SendResult

if TYPE_CHECKING:
    from apps.notifications.models import Notification, NotificationDelivery


class EmailChannel:
    name = "email"

    def send(self, notification: Notification, delivery: NotificationDelivery) -> SendResult:
        recipient = notification.user.email
        if not recipient:
            return SendResult(ok=False, error="User has no email address.")
        send_mail(
            subject=notification.title,
            message=notification.body or notification.title,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
        )
        return SendResult(ok=True, provider_id="email")
