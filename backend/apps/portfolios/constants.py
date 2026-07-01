"""Portfolio enums."""

from __future__ import annotations

from django.db import models


class TransactionType(models.TextChoices):
    BUY = "buy", "Buy"
    SELL = "sell", "Sell"
