"""YahooProvider parsing + graceful synthetic fallback (no real network)."""

from __future__ import annotations

from integrations.market_data import yahoo as yahoo_mod
from integrations.market_data.yahoo import YahooProvider

_QUOTE_JSON = {
    "chart": {"result": [{"meta": {"regularMarketPrice": 289.36, "chartPreviousClose": 312.06}}]}
}

_HISTORY_JSON = {
    "chart": {
        "result": [
            {
                "timestamp": [1719273600, 1719360000, 1719446400],
                "indicators": {
                    "quote": [
                        {
                            "open": [1.070, 1.075, None],
                            "high": [1.080, 1.079, 1.081],
                            "low": [1.060, 1.070, 1.069],
                            "close": [1.075, 1.078, None],
                        }
                    ]
                },
            }
        ]
    }
}


def test_quote_parses_yahoo_json(monkeypatch):
    monkeypatch.setattr(yahoo_mod, "_http_get_json", lambda url: _QUOTE_JSON)
    quote = YahooProvider().get_quote("AAPL")
    assert quote.price == 289.36
    assert round(quote.change, 2) == round(289.36 - 312.06, 2)
    assert quote.change_percent < 0  # price below previous close


def test_history_parses_and_skips_nulls(monkeypatch):
    monkeypatch.setattr(yahoo_mod, "_http_get_json", lambda url: _HISTORY_JSON)
    bars = YahooProvider().get_history("EURUSD=X", "1d", 10)
    # Third point has a null close -> skipped.
    assert len(bars) == 2
    assert bars[-1].close == 1.078


def test_quote_falls_back_to_synthetic_on_error(monkeypatch):
    def boom(url):
        raise OSError("network down")

    monkeypatch.setattr(yahoo_mod, "_http_get_json", boom)
    quote = YahooProvider().get_quote("XAUUSD")
    assert quote.price > 0
    assert quote.symbol == "XAUUSD"


def test_history_falls_back_to_synthetic_on_error(monkeypatch):
    def boom(url):
        raise OSError("network down")

    monkeypatch.setattr(yahoo_mod, "_http_get_json", boom)
    bars = YahooProvider().get_history("XAUUSD", "1d", 30)
    assert len(bars) == 30


def test_non_daily_interval_uses_fallback(monkeypatch):
    def boom(url):
        raise AssertionError("should not fetch")

    monkeypatch.setattr(yahoo_mod, "_http_get_json", boom)
    bars = YahooProvider().get_history("EURUSD=X", "1h", 24)
    assert len(bars) == 24
