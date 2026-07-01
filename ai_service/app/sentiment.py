"""Lightweight finance sentiment (lexicon). FinBERT can swap in behind this API."""
from __future__ import annotations

import re

_WORD = re.compile(r"[a-z']+")

_POSITIVE = {
    "surge", "surges", "soar", "gain", "gains", "rally", "jump", "beat", "beats",
    "record", "growth", "profit", "upgrade", "bullish", "strong", "boost", "rises",
    "outperform", "optimistic", "recovery", "higher",
}
_NEGATIVE = {
    "plunge", "slump", "fall", "falls", "drop", "loss", "losses", "miss", "crash",
    "downgrade", "bearish", "weak", "decline", "fear", "fears", "selloff", "cut",
    "lower", "warning", "underperform",
}


def analyze(text: str) -> dict:
    tokens = _WORD.findall(text.lower())
    pos = sum(1 for t in tokens if t in _POSITIVE)
    neg = sum(1 for t in tokens if t in _NEGATIVE)
    total = pos + neg
    score = 0.0 if total == 0 else (pos - neg) / total
    label = "positive" if score > 0.15 else "negative" if score < -0.15 else "neutral"
    return {
        "label": label,
        "score": round(score, 4),
        "confidence": round(min(1.0, total / 5.0), 2),
        "model": "lexicon-v1",
    }
