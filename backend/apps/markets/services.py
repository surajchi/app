"""Read-side services for quotes, history, and movers."""

from __future__ import annotations

import datetime as dt
from typing import Any

from apps.markets import cache
from apps.markets.models import Instrument, PriceBar


def latest_quote(instrument: Instrument) -> dict[str, Any] | None:
    """Live quote from cache, falling back to the last stored bar (flagged stale)."""
    cached = cache.get_quote(instrument.id)
    if cached is not None:
        return cached
    bar = PriceBar.objects.filter(instrument=instrument).order_by("-ts").first()
    if bar is None:
        return None
    return {
        "price": float(bar.close),
        "change": 0.0,
        "change_percent": 0.0,
        "volume": float(bar.volume or 0),
        "ts": bar.ts.isoformat(),
        "stale": True,
    }


def history(
    instrument: Instrument,
    interval: str,
    start: dt.datetime | None = None,
    end: dt.datetime | None = None,
    limit: int = 1000,
) -> list[PriceBar]:
    qs = PriceBar.objects.filter(instrument=instrument, interval=interval)
    if start is not None:
        qs = qs.filter(ts__gte=start)
    if end is not None:
        qs = qs.filter(ts__lte=end)
    return list(qs.order_by("ts")[:limit])


def movers(
    asset_class: str | None = None, kind: str = "gainers", limit: int = 10
) -> list[dict[str, Any]]:
    qs = Instrument.objects.filter(is_active=True)
    if asset_class:
        qs = qs.filter(asset_class=asset_class)

    rows: list[dict[str, Any]] = []
    for instrument in qs.select_related("exchange")[:500]:
        quote = cache.get_quote(instrument.id)
        if quote is None:
            continue
        rows.append({"instrument": instrument, "quote": quote})

    rows.sort(key=lambda row: row["quote"].get("change_percent", 0.0), reverse=kind != "losers")
    return rows[:limit]


def market_breadth() -> dict[str, Any]:
    """Advancers/decliners and average move across instruments with a live quote."""
    advancers = decliners = counted = 0
    total_change = 0.0
    for instrument in Instrument.objects.filter(is_active=True).only("id"):
        quote = cache.get_quote(instrument.id)
        if not quote:
            continue
        change_pct = quote.get("change_percent")
        if change_pct is None:
            continue
        counted += 1
        total_change += change_pct
        if change_pct > 0:
            advancers += 1
        elif change_pct < 0:
            decliners += 1
    avg_change = round(total_change / counted, 4) if counted else 0.0
    return {
        "advancers": advancers,
        "decliners": decliners,
        "counted": counted,
        "avg_change": avg_change,
    }
