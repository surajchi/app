"""Scheduled billing task: renew due subscriptions and expire canceled ones."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger("finpulse")


@shared_task(name="apps.billing.tasks.process_renewals")
def process_renewals() -> dict[str, int]:
    from apps.billing.services import process_renewals as run

    return run()
