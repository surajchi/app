"""Celery notification dispatch with per-delivery status + retry."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger("finpulse")


@shared_task(
    bind=True,
    name="apps.notifications.tasks.dispatch_notification",
    max_retries=3,
    default_retry_delay=10,
)
def dispatch_notification(self, notification_id: str) -> int:
    from django.utils import timezone

    from apps.notifications.channels import registry
    from apps.notifications.channels.base import SendResult
    from apps.notifications.constants import DeliveryStatus
    from apps.notifications.models import Notification

    try:
        notification = Notification.objects.select_related("user").get(id=notification_id)
    except Notification.DoesNotExist:
        return 0

    pending = notification.deliveries.exclude(
        status__in=[DeliveryStatus.DELIVERED, DeliveryStatus.SKIPPED]
    )
    delivered = 0
    failed = False

    for delivery in pending:
        delivery.attempts += 1
        channel = registry.get_channel(delivery.channel)
        if channel is None:
            delivery.status = DeliveryStatus.SKIPPED
            delivery.save(update_fields=["status", "attempts", "updated_at"])
            continue

        try:
            result = channel.send(notification, delivery)
        except Exception as exc:  # noqa: BLE001 - convert any channel error to a failed result
            result = SendResult(ok=False, error=str(exc))

        if result.ok:
            delivery.status = DeliveryStatus.DELIVERED
            delivery.provider_message_id = result.provider_id[:255]
            delivery.sent_at = timezone.now()
            delivered += 1
        else:
            failed = True
            can_retry = self.request.retries < self.max_retries
            delivery.status = DeliveryStatus.RETRYING if can_retry else DeliveryStatus.FAILED
            delivery.error = (result.error or "")[:500]
        delivery.save(
            update_fields=[
                "status",
                "attempts",
                "provider_message_id",
                "sent_at",
                "error",
                "updated_at",
            ]
        )

    if failed and self.request.retries < self.max_retries:
        raise self.retry()
    return delivered
