"""News domain enums + NLP lexicons/weights (dependency-free)."""

from __future__ import annotations

from django.db import models


class Sentiment(models.TextChoices):
    POSITIVE = "positive", "Positive"
    NEGATIVE = "negative", "Negative"
    NEUTRAL = "neutral", "Neutral"


class EntityType(models.TextChoices):
    INSTRUMENT = "instrument", "Instrument"
    COMPANY = "company", "Company"
    TICKER = "ticker", "Ticker"
    CURRENCY = "currency", "Currency"
    COMMODITY = "commodity", "Commodity"
    COUNTRY = "country", "Country"
    PERSON = "person", "Person"
    ORG = "org", "Organization"


class ArticleStatus(models.TextChoices):
    INGESTED = "ingested", "Ingested"
    PROCESSED = "processed", "Processed"
    PUBLISHED = "published", "Published"
    REJECTED = "rejected", "Rejected"


# Default categories (slug -> display name).
DEFAULT_CATEGORIES = {
    "markets": "Markets",
    "economy": "Economy",
    "earnings": "Earnings",
    "crypto": "Crypto",
    "commodities": "Commodities",
    "forex": "Forex",
    "general": "General",
}

# Keyword -> category for the lightweight categorizer (first match wins).
CATEGORY_KEYWORDS = {
    "earnings": ["earnings", "profit", "revenue", "guidance", "quarterly results", "eps"],
    "crypto": ["bitcoin", "btc", "ethereum", "crypto", "blockchain", "token"],
    "commodities": ["gold", "oil", "crude", "silver", "commodity", "metals"],
    "forex": ["forex", "currency", "dollar", "rupee", "euro", "exchange rate"],
    "economy": ["inflation", "gdp", "rate cut", "rate hike", "central bank", "rbi", "fed", "cpi"],
    "markets": ["stock", "shares", "index", "nifty", "sensex", "nasdaq", "rally", "selloff"],
}

# Finance sentiment lexicon (lowercase).
POSITIVE_WORDS = {
    "surge",
    "surges",
    "soar",
    "soars",
    "gain",
    "gains",
    "rally",
    "rallies",
    "jump",
    "jumps",
    "rise",
    "rises",
    "beat",
    "beats",
    "record",
    "growth",
    "profit",
    "upgrade",
    "bullish",
    "outperform",
    "strong",
    "boost",
    "optimistic",
    "recovery",
    "wins",
    "high",
    "higher",
}
NEGATIVE_WORDS = {
    "plunge",
    "plunges",
    "slump",
    "slumps",
    "fall",
    "falls",
    "drop",
    "drops",
    "loss",
    "losses",
    "miss",
    "misses",
    "crash",
    "crashes",
    "downgrade",
    "bearish",
    "underperform",
    "weak",
    "decline",
    "declines",
    "fear",
    "fears",
    "selloff",
    "cut",
    "cuts",
    "low",
    "lower",
    "warning",
}

# Relative authority of sources for impact scoring (default 0.5).
SOURCE_WEIGHTS = {
    "reuters": 1.0,
    "bloomberg": 1.0,
    "synthetic": 0.6,
    "rss": 0.6,
}

NEAR_DUPLICATE_HAMMING = 3  # simhash distance under which articles are duplicates
