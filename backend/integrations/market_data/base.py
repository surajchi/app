"""Provider-agnostic value objects and the market-data provider interface.

This is the anti-corruption boundary: the rest of the app depends only on these
types, never on a vendor's payload shape.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Protocol, runtime_checkable


@dataclasses.dataclass(frozen=True)
class Quote:
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: float
    ts: dt.datetime


@dataclasses.dataclass(frozen=True)
class Bar:
    ts: dt.datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@runtime_checkable
class MarketDataProvider(Protocol):
    name: str

    def get_quote(self, symbol: str) -> Quote: ...

    def get_history(self, symbol: str, interval: str, periods: int) -> list[Bar]: ...
