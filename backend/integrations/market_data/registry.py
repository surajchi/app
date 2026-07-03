"""Resolve the active market-data provider (defaults to the synthetic one)."""

from __future__ import annotations

from django.conf import settings

from integrations.market_data.base import MarketDataProvider
from integrations.market_data.synthetic import SyntheticProvider
from integrations.market_data.yahoo import YahooProvider

_PROVIDERS: dict[str, type] = {
    "synthetic": SyntheticProvider,
    "yahoo": YahooProvider,
}


def get_provider(name: str | None = None) -> MarketDataProvider:
    name = name or getattr(settings, "MARKET_DATA_PROVIDER", "synthetic")
    provider_cls = _PROVIDERS.get(str(name), SyntheticProvider)
    return provider_cls()
