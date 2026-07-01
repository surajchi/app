"""Pluggable news sentiment: lexicon (default) or the AI service, with fallback.

Configured via settings.NEWS_SENTIMENT_BACKEND ("lexicon" | "ai_service").
Phase 5 lets news use the AI service's model without changing the pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

from apps.news.nlp import analyzers

logger = logging.getLogger("finpulse")


def analyze_sentiment(text: str) -> dict[str, Any]:
    if getattr(settings, "NEWS_SENTIMENT_BACKEND", "lexicon") == "ai_service":
        try:
            from apps.ai import client

            result = client.sentiment(text)
            return {
                "label": str(result["label"]),
                "score": float(result["score"]),
                "confidence": float(result["confidence"]),
                "analyzer": str(result.get("model", "ai_service")),
            }
        except Exception:  # noqa: BLE001 - fall back to the local lexicon on any failure
            logger.exception("news.sentiment_ai_failed")
    return analyzers.analyze_sentiment(text)
