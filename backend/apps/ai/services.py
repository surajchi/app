"""AI proxy services: fetch price history, call the AI service, persist + cache."""

from __future__ import annotations

from typing import Any

from django.core.cache import cache

from apps.ai import client
from apps.ai.models import AIPrediction
from apps.markets.models import Instrument, PriceBar

_HISTORY_LIMIT = 120


def _closes(instrument: Instrument) -> list[float]:
    values = (
        PriceBar.objects.filter(instrument=instrument, interval="1d")
        .order_by("ts")
        .values_list("close", flat=True)
    )
    return [float(c) for c in values][-_HISTORY_LIMIT:]


def get_forecast(instrument: Instrument, horizon: int = 7) -> dict[str, Any]:
    key = f"ai:forecast:{instrument.id}:{horizon}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    result = client.forecast(_closes(instrument), horizon)
    AIPrediction.objects.create(
        instrument=instrument,
        prediction_type="price_forecast",
        horizon=f"{horizon}d",
        value=result,
        confidence=float(result.get("confidence", 0.0)),
        model=str(result.get("model", "")),
    )
    payload = {
        **result,
        "symbol": instrument.symbol,
        "horizon": f"{horizon}d",
        "disclaimer": "Not financial advice.",
    }
    cache.set(key, payload, 300)
    return payload


def get_technical(instrument: Instrument) -> dict[str, Any]:
    key = f"ai:technical:{instrument.id}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    result = client.technical(_closes(instrument))
    AIPrediction.objects.create(
        instrument=instrument,
        prediction_type="technical",
        value=result,
        confidence=float(result.get("strength", 0.0)),
        model=str(result.get("model", "")),
    )
    payload = {**result, "symbol": instrument.symbol, "disclaimer": "Not financial advice."}
    cache.set(key, payload, 120)
    return payload
