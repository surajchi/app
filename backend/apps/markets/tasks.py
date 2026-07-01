"""Celery ingestion tasks for market data."""

from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from apps.markets import cache
from apps.markets.models import DataProviderStatus, Instrument, SymbolAlias
from integrations.market_data.registry import get_provider

logger = logging.getLogger("finpulse")


def _provider_symbol(instrument: Instrument, provider_name: str) -> str:
    alias = SymbolAlias.objects.filter(instrument=instrument, provider=provider_name).first()
    return alias.provider_symbol if alias else instrument.symbol


@shared_task(name="apps.markets.tasks.poll_quotes")
def poll_quotes() -> int:
    """Fetch the latest quote for every active instrument into the cache."""
    # Imported lazily so the Channels/ASGI stack isn't pulled in during Celery's
    # task autodiscovery (which runs before the Django app registry is ready).
    from realtime.publish import publish_quote

    provider = get_provider()
    polled = 0
    for instrument in Instrument.objects.filter(is_active=True).iterator():
        try:
            quote = provider.get_quote(_provider_symbol(instrument, provider.name))
        except Exception:  # noqa: BLE001 - one bad symbol must not stop the sweep
            logger.exception("market.poll_failed", extra={"instrument": str(instrument.id)})
            continue
        payload = {
            "symbol": instrument.symbol,
            "price": quote.price,
            "change": quote.change,
            "change_percent": quote.change_percent,
            "volume": quote.volume,
            "ts": quote.ts.isoformat(),
        }
        cache.set_quote(instrument.id, payload)
        publish_quote(instrument.symbol, payload)
        polled += 1

    DataProviderStatus.objects.update_or_create(
        provider=provider.name,
        defaults={
            "domain": "market",
            "status": DataProviderStatus.Status.OK,
            "last_success_at": timezone.now(),
        },
    )
    logger.info("market.polled", extra={"count": polled})
    return polled
