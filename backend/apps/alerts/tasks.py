"""Celery task: evaluate price alerts against the latest quotes on a schedule."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger("finpulse")


@shared_task(name="apps.alerts.tasks.evaluate_price_alerts")
def evaluate_price_alerts() -> int:
    from apps.alerts.services import evaluate_price_rules

    fired = evaluate_price_rules()
    if fired:
        logger.info("alerts.price_evaluated", extra={"fired": fired})
    return fired
