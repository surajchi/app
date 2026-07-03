"""Yahoo Finance market-data provider — real quotes/history, free and keyless.

Uses the public chart endpoint (JSON, no API key, no signup):
  https://query1.finance.yahoo.com/v8/finance/chart/<sym>?interval=1d&range=1y

Returns both the latest price (``meta.regularMarketPrice``) and daily OHLC
history. Best-effort: any error or missing data falls back to the deterministic
synthetic provider so the platform always has a price to show. Callers pass the
Yahoo symbol (resolved via SymbolAlias, e.g. EURUSD -> EURUSD=X).
"""

from __future__ import annotations

import datetime as dt
import json
import urllib.parse
import urllib.request

from django.utils import timezone

from integrations.market_data.base import Bar, Quote
from integrations.market_data.synthetic import SyntheticProvider

_TIMEOUT = 8
_UA = "Mozilla/5.0 (FinPulse market-data fetcher)"
_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"


def _http_get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:  # noqa: S310
        return json.loads(response.read())


def _result(symbol: str, params: str) -> dict:
    url = f"{_BASE}{urllib.parse.quote(symbol)}?{params}"
    payload = _http_get_json(url)
    results = (payload.get("chart") or {}).get("result") or []
    if not results:
        raise ValueError("no chart result")
    return results[0]


class YahooProvider:
    name = "yahoo"

    def __init__(self) -> None:
        self._fallback = SyntheticProvider()

    def get_quote(self, symbol: str) -> Quote:
        try:
            return self._fetch_quote(symbol)
        except Exception:  # noqa: BLE001 - any failure -> deterministic fallback
            return self._fallback.get_quote(symbol)

    def get_history(self, symbol: str, interval: str, periods: int) -> list[Bar]:
        if interval != "1d":
            return self._fallback.get_history(symbol, interval, periods)
        try:
            bars = self._fetch_history(symbol, periods)
            if not bars:
                raise ValueError("no bars")
            return bars
        except Exception:  # noqa: BLE001
            return self._fallback.get_history(symbol, interval, periods)

    def _fetch_quote(self, symbol: str) -> Quote:
        meta = _result(symbol, "interval=1d&range=5d").get("meta") or {}
        price = meta.get("regularMarketPrice")
        if price is None:
            raise ValueError("no price")
        price = float(price)
        prev = meta.get("chartPreviousClose") or meta.get("previousClose") or price
        prev = float(prev)
        change = round(price - prev, 6)
        change_pct = round((change / prev) * 100, 4) if prev else 0.0
        volume = float(meta.get("regularMarketVolume") or 0)
        return Quote(
            symbol=symbol,
            price=round(price, 6),
            change=change,
            change_percent=change_pct,
            volume=volume,
            ts=timezone.now(),
        )

    def _fetch_history(self, symbol: str, periods: int) -> list[Bar]:
        result = _result(symbol, "interval=1d&range=1y")
        stamps = result.get("timestamp") or []
        quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
        opens, highs = quote.get("open") or [], quote.get("high") or []
        lows, closes = quote.get("low") or [], quote.get("close") or []

        bars: list[Bar] = []
        for i, stamp in enumerate(stamps):
            close = closes[i] if i < len(closes) else None
            if close is None:
                continue
            open_ = opens[i] if i < len(opens) and opens[i] is not None else close
            high = highs[i] if i < len(highs) and highs[i] is not None else close
            low = lows[i] if i < len(lows) and lows[i] is not None else close
            bars.append(
                Bar(
                    ts=dt.datetime.fromtimestamp(stamp, tz=dt.UTC),
                    open=float(open_),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    volume=0.0,
                )
            )
        return bars[-periods:]
