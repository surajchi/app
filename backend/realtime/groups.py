"""Channel-layer group name helpers (names must match [a-zA-Z0-9-_.], <100 chars)."""

from __future__ import annotations

import re

_SAFE = re.compile(r"[^a-zA-Z0-9._-]")

QUOTE_PREFIX = "quotes."


def quote_group(symbol: str) -> str:
    return f"{QUOTE_PREFIX}{_SAFE.sub('-', symbol.upper())}"[:99]


def alerts_group(user_id: str) -> str:
    return f"alerts.{_SAFE.sub('-', str(user_id))}"[:99]


def news_group(category: str | None = None) -> str:
    if category:
        return f"news.{_SAFE.sub('-', category)}"[:99]
    return "news"
