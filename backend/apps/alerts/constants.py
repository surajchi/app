"""Alert rule enums and trigger groupings."""

from __future__ import annotations

from django.db import models


class TriggerType(models.TextChoices):
    PRICE_ABOVE = "price_above", "Price above"
    PRICE_BELOW = "price_below", "Price below"
    PCT_CHANGE = "pct_change", "Percent change"
    NEWS_KEYWORD = "news_keyword", "News keyword"
    SENTIMENT = "sentiment", "News sentiment"


# Grouped for evaluation + validation, as plain string values (str(Member))
# so they type-check as tuple[str, ...] and compare against stored values.
PRICE_TRIGGERS: tuple[str, ...] = (
    str(TriggerType.PRICE_ABOVE),
    str(TriggerType.PRICE_BELOW),
    str(TriggerType.PCT_CHANGE),
)
NEWS_TRIGGERS: tuple[str, ...] = (
    str(TriggerType.NEWS_KEYWORD),
    str(TriggerType.SENTIMENT),
)


class Frequency(models.TextChoices):
    ONCE = "once", "Once"  # fire once, then deactivate
    RECURRING = "recurring", "Recurring"  # re-arm after each fire (subject to cooldown)


class AlertStatus(models.TextChoices):
    SENT = "sent", "Sent"
    SUPPRESSED = "suppressed", "Suppressed"
