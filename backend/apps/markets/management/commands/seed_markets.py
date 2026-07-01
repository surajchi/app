"""Seed exchanges + a small multi-asset instrument universe and backfill history.

Idempotent: safe to run repeatedly. Run with:
    python manage.py seed_markets
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand

from apps.markets import cache
from apps.markets.constants import AssetClass, Interval
from apps.markets.models import Exchange, Instrument, Market, PriceBar
from integrations.market_data.registry import get_provider

EXCHANGES = [
    {"code": "NASDAQ", "name": "Nasdaq", "country": "US", "currency": "USD"},
    {"code": "NYSE", "name": "New York Stock Exchange", "country": "US", "currency": "USD"},
    {"code": "NSE", "name": "National Stock Exchange of India", "country": "IN", "currency": "INR"},
]

# (asset_class, symbol, name, exchange_code, currency)
INSTRUMENTS = [
    (AssetClass.STOCK, "AAPL", "Apple Inc.", "NASDAQ", "USD"),
    (AssetClass.STOCK, "MSFT", "Microsoft Corp.", "NASDAQ", "USD"),
    (AssetClass.STOCK, "RELIANCE", "Reliance Industries", "NSE", "INR"),
    (AssetClass.ETF, "SPY", "SPDR S&P 500 ETF", "NYSE", "USD"),
    (AssetClass.INDEX, "NIFTY50", "Nifty 50", "NSE", "INR"),
    (AssetClass.INDEX, "SPX", "S&P 500 Index", None, "USD"),
    (AssetClass.FOREX, "EURUSD", "Euro / US Dollar", None, "USD"),
    (AssetClass.FOREX, "USDINR", "US Dollar / Indian Rupee", None, "INR"),
    (AssetClass.COMMODITY, "XAUUSD", "Gold Spot", None, "USD"),
    (AssetClass.CRYPTO, "BTCUSD", "Bitcoin", None, "USD"),
]

BACKFILL_PERIODS = 180  # ~6 months of daily bars


class Command(BaseCommand):
    help = "Seed market reference data and backfill historical bars."

    def handle(self, *args: Any, **options: Any) -> None:
        for code, ac in [("EQ", AssetClass.STOCK), ("FX", AssetClass.FOREX)]:
            Market.objects.get_or_create(code=code, defaults={"name": code, "asset_class": ac})

        exchanges: dict[str, Exchange] = {}
        for data in EXCHANGES:
            exchange, _ = Exchange.objects.get_or_create(code=data["code"], defaults=data)
            exchanges[data["code"]] = exchange

        provider = get_provider()
        created = 0
        for asset_class, symbol, name, exchange_code, currency in INSTRUMENTS:
            instrument, was_created = Instrument.objects.get_or_create(
                asset_class=asset_class,
                symbol=symbol,
                exchange=exchanges.get(exchange_code) if exchange_code else None,
                defaults={"name": name, "currency": currency},
            )
            created += int(was_created)

            interval = str(Interval.D1)
            if not PriceBar.objects.filter(instrument=instrument, interval=interval).exists():
                bars = provider.get_history(symbol, interval, BACKFILL_PERIODS)
                PriceBar.objects.bulk_create(
                    [
                        PriceBar(
                            instrument=instrument,
                            interval=interval,
                            ts=bar.ts,
                            open=Decimal(str(bar.open)),
                            high=Decimal(str(bar.high)),
                            low=Decimal(str(bar.low)),
                            close=Decimal(str(bar.close)),
                            volume=Decimal(str(bar.volume)),
                            source=provider.name,
                        )
                        for bar in bars
                    ],
                    ignore_conflicts=True,
                )

            # Warm the latest-quote cache so /quote and /movers work immediately.
            quote = provider.get_quote(symbol)
            cache.set_quote(
                instrument.id,
                {
                    "price": quote.price,
                    "change": quote.change,
                    "change_percent": quote.change_percent,
                    "volume": quote.volume,
                    "ts": quote.ts.isoformat(),
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Instrument.objects.count()} instruments "
                f"({created} new), backfilled history, warmed quote cache."
            )
        )
