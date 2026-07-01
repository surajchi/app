"""Latest-quote cache. Backed by Django's cache (Redis in prod, locmem in tests)."""

from __future__ import annotations

from typing import Any

from django.core.cache import cache

QUOTE_PREFIX = "market:quote:"
QUOTE_TTL = 3600  # seconds


def _key(instrument_id: Any) -> str:
    return f"{QUOTE_PREFIX}{instrument_id}"


def set_quote(instrument_id: Any, data: dict[str, Any]) -> None:
    cache.set(_key(instrument_id), data, QUOTE_TTL)


def get_quote(instrument_id: Any) -> dict[str, Any] | None:
    return cache.get(_key(instrument_id))
