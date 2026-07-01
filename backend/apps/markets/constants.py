"""Market domain enums and constants."""

from __future__ import annotations

from django.db import models


class AssetClass(models.TextChoices):
    STOCK = "stock", "Stock"
    FOREX = "forex", "Forex"
    COMMODITY = "commodity", "Commodity"
    INDEX = "index", "Index"
    ETF = "ETF", "ETF"
    CRYPTO = "crypto", "Crypto"


class Interval(models.TextChoices):
    M1 = "1m", "1 minute"
    M5 = "5m", "5 minutes"
    M15 = "15m", "15 minutes"
    H1 = "1h", "1 hour"
    D1 = "1d", "1 day"


# Intervals exposed by the history endpoint (kept as literals for type-checking;
# they mirror the Interval choices above).
VALID_INTERVALS = {"1m", "5m", "15m", "1h", "1d"}

DEFAULT_HISTORY_INTERVAL = "1d"
