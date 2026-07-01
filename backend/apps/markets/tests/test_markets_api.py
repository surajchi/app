import datetime as dt

import pytest
from django.core.cache import cache as dj_cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.markets import cache
from apps.markets.models import DataProviderStatus, PriceBar
from apps.markets.tasks import poll_quotes
from apps.markets.tests.factories import ExchangeFactory, InstrumentFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    dj_cache.clear()
    yield
    dj_cache.clear()


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _make_bars(instrument, n=5, interval="1d"):
    base = timezone.now() - dt.timedelta(days=n)
    for i in range(n):
        PriceBar.objects.create(
            instrument=instrument,
            interval=interval,
            ts=base + dt.timedelta(days=i),
            open=100 + i,
            high=101 + i,
            low=99 + i,
            close=100 + i,
            volume=1000,
        )


def test_list_instruments(client):
    InstrumentFactory(symbol="AAA")
    InstrumentFactory(symbol="BBB", asset_class="forex")
    resp = client.get("/api/v1/markets/instruments/")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2


def test_filter_by_asset_class(client):
    InstrumentFactory(symbol="STK", asset_class="stock")
    InstrumentFactory(symbol="FX1", asset_class="forex")
    resp = client.get("/api/v1/markets/instruments/?asset_class=forex")
    symbols = [row["symbol"] for row in resp.json()["data"]]
    assert "FX1" in symbols and "STK" not in symbols


def test_search_instruments(client):
    InstrumentFactory(symbol="ZZZ", name="Zeta Corp")
    resp = client.get("/api/v1/markets/instruments/?search=Zeta")
    assert any(row["symbol"] == "ZZZ" for row in resp.json()["data"])


def test_instrument_detail_and_404(client):
    InstrumentFactory(symbol="DET")
    assert client.get("/api/v1/markets/instruments/DET/").status_code == 200
    assert client.get("/api/v1/markets/instruments/NOPE/").status_code == 404


def test_quote_from_cache(client):
    instrument = InstrumentFactory(symbol="QQQ")
    cache.set_quote(
        instrument.id,
        {"price": 123.4, "change": 1.2, "change_percent": 1.0, "volume": 1000, "ts": "t"},
    )
    resp = client.get("/api/v1/markets/instruments/QQQ/quote/")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["price"] == 123.4
    assert data["symbol"] == "QQQ"


def test_quote_falls_back_to_last_bar(client):
    instrument = InstrumentFactory(symbol="FBK")
    _make_bars(instrument, 3)
    resp = client.get("/api/v1/markets/instruments/FBK/quote/")
    assert resp.status_code == 200
    assert resp.json()["data"]["stale"] is True


def test_history(client):
    instrument = InstrumentFactory(symbol="HST")
    _make_bars(instrument, 5)
    resp = client.get("/api/v1/markets/instruments/HST/history/?interval=1d")
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["interval"] == "1d"
    assert len(body["candles"]) == 5
    assert {"ts", "open", "high", "low", "close", "volume"} <= set(body["candles"][0])


def test_history_invalid_interval(client):
    InstrumentFactory(symbol="BAD")
    resp = client.get("/api/v1/markets/instruments/BAD/history/?interval=2y")
    assert resp.status_code == 400


def test_movers(client):
    up = InstrumentFactory(symbol="UP")
    down = InstrumentFactory(symbol="DN")
    cache.set_quote(
        up.id, {"price": 10, "change": 1, "change_percent": 5.0, "volume": 1, "ts": "t"}
    )
    cache.set_quote(
        down.id, {"price": 10, "change": -1, "change_percent": -5.0, "volume": 1, "ts": "t"}
    )
    gainers = client.get("/api/v1/markets/movers/?type=gainers").json()["data"]
    assert gainers["results"][0]["symbol"] == "UP"
    losers = client.get("/api/v1/markets/movers/?type=losers").json()["data"]
    assert losers["results"][0]["symbol"] == "DN"


def test_poll_quotes_task_populates_cache(client):
    instrument = InstrumentFactory(symbol="POLL")
    polled = poll_quotes()
    assert polled >= 1
    assert cache.get_quote(instrument.id) is not None
    assert DataProviderStatus.objects.filter(provider="synthetic").exists()


def test_exchanges(client):
    ExchangeFactory(code="XNAS")
    resp = client.get("/api/v1/markets/exchanges/")
    assert resp.status_code == 200
    assert any(row["code"] == "XNAS" for row in resp.json()["data"])
