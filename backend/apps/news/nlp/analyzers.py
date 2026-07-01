"""Lightweight, dependency-free text analyzers.

These are deterministic stand-ins for the heavy models (FinBERT, summarizers)
that move into the FastAPI AI service in Phase 5. The pipeline depends on these
function signatures, so swapping in the real models is a drop-in change.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from apps.news.constants import (
    CATEGORY_KEYWORDS,
    NEGATIVE_WORDS,
    POSITIVE_WORDS,
    SOURCE_WEIGHTS,
    Sentiment,
)

_WORD = re.compile(r"[a-z0-9]+")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_SIMHASH_BITS = 63  # keep within a positive signed BIGINT


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


# --- near-duplicate detection ----------------------------------------------


def simhash(text: str) -> int:
    tokens = _tokens(text)
    if not tokens:
        return 0
    vector = [0] * _SIMHASH_BITS
    for token in tokens:
        digest = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(_SIMHASH_BITS):
            vector[i] += 1 if (digest >> i) & 1 else -1
    result = 0
    for i in range(_SIMHASH_BITS):
        if vector[i] > 0:
            result |= 1 << i
    return result


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


# --- sentiment --------------------------------------------------------------


def analyze_sentiment(text: str) -> dict[str, Any]:
    tokens = _tokens(text)
    positive = sum(1 for t in tokens if t in POSITIVE_WORDS)
    negative = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    total = positive + negative
    score = 0.0 if total == 0 else (positive - negative) / total
    if score > 0.15:
        label = Sentiment.POSITIVE
    elif score < -0.15:
        label = Sentiment.NEGATIVE
    else:
        label = Sentiment.NEUTRAL
    return {
        "label": str(label),
        "score": round(score, 4),
        "confidence": round(min(1.0, total / 5.0), 2),
        "analyzer": "lexicon",
    }


# --- categorization ---------------------------------------------------------


def categorize(text: str) -> str:
    low = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in low for keyword in keywords):
            return category
    return "general"


# --- summarization (extractive) --------------------------------------------


def summarize(title: str, body: str, max_sentences: int = 2) -> str:
    text = body.strip() or title.strip()
    sentences = [s.strip() for s in _SENTENCE.split(text) if s.strip()]
    return " ".join(sentences[:max_sentences])


# --- impact scoring ---------------------------------------------------------


def impact_score(source: str, sentiment_score: float, entity_count: int) -> int:
    source_weight = SOURCE_WEIGHTS.get(source.lower(), 0.5)
    magnitude = min(1.0, abs(sentiment_score))
    entity_factor = min(1.0, entity_count / 3)
    raw = 0.4 * source_weight + 0.4 * magnitude + 0.2 * entity_factor
    return int(round(raw * 100))
