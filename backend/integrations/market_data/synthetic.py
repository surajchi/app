"""Deterministic synthetic market-data provider.

Generates plausible, repeatable quotes/bars from a symbol seed so the platform
is fully runnable and testable without any external API keys. Swap for a real
provider via MARKET_DATA_PROVIDER + a new adapter implementing MarketDataProvider.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import random

from django.utils import timezone

from integrations.market_data.base import Bar, Quote

_INTERVAL_DELTA: dict[str, dt.timedelta] = {
    "1m": dt.timedelta(minutes=1),
    "5m": dt.timedelta(minutes=5),
    "15m": dt.timedelta(minutes=15),
    "1h": dt.timedelta(hours=1),
    "1d": dt.timedelta(days=1),
}


def _seeded_rng(*parts: str) -> random.Random:
    digest = hashlib.sha256(":".join(parts).encode()).hexdigest()
    return random.Random(int(digest, 16))


class SyntheticProvider:
    name = "synthetic"

    def _base_price(self, symbol: str) -> float:
        digest = int(hashlib.sha256(symbol.encode()).hexdigest(), 16)
        return 50.0 + (digest % 50_000) / 100.0  # ~50 .. 550

    def _day_open(self, symbol: str, when: dt.datetime) -> float:
        rng = _seeded_rng(symbol, when.strftime("%Y-%m-%d"))
        return round(self._base_price(symbol) * (1 + rng.uniform(-0.03, 0.03)), 4)

    def get_quote(self, symbol: str) -> Quote:
        now = timezone.now()
        day_open = self._day_open(symbol, now)
        rng = _seeded_rng(symbol, now.strftime("%Y-%m-%d %H:%M"))
        price = round(day_open * (1 + rng.uniform(-0.02, 0.02)), 4)
        change = round(price - day_open, 4)
        change_pct = round((change / day_open) * 100, 4) if day_open else 0.0
        return Quote(
            symbol=symbol,
            price=price,
            change=change,
            change_percent=change_pct,
            volume=float(rng.randint(1_000, 1_000_000)),
            ts=now,
        )

    def get_history(self, symbol: str, interval: str, periods: int) -> list[Bar]:
        delta = _INTERVAL_DELTA.get(interval, dt.timedelta(days=1))
        start = timezone.now() - delta * periods
        price = self._base_price(symbol)
        bars: list[Bar] = []
        for i in range(periods):
            ts = start + delta * i
            rng = _seeded_rng(symbol, interval, ts.isoformat())
            open_ = price
            close = max(0.01, round(open_ * (1 + rng.uniform(-0.02, 0.02)), 4))
            high = round(max(open_, close) * (1 + abs(rng.uniform(0, 0.01))), 4)
            low = round(min(open_, close) * (1 - abs(rng.uniform(0, 0.01))), 4)
            bars.append(Bar(ts, open_, high, low, close, float(rng.randint(1_000, 5_000_000))))
            price = close
        return bars
