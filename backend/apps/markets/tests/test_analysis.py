import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.ai.client import AIServiceError
from apps.markets import cache as market_cache
from apps.markets.tests.factories import InstrumentFactory
from apps.news.models import NewsArticle, NewsEntity, NewsSentiment
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

_FORECAST = {
    "points": [{"step": 1, "mean": 110.0, "low": 105.0, "high": 115.0}],
    "confidence": 0.6,
    "model": "linreg-v1",
    "horizon": "7d",
}
_TECHNICAL = {
    "indicators": {"rsi": 65.0, "macd": 1.2, "macd_signal": 0.8, "sma20": 98.0, "price": 100.0},
    "signal": "buy",
    "strength": 0.67,
    "model": "ta-v1",
}


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def ai_up(monkeypatch):
    monkeypatch.setattr("apps.ai.services.get_forecast", lambda instrument, horizon=7: _FORECAST)
    monkeypatch.setattr("apps.ai.services.get_technical", lambda instrument: _TECHNICAL)


@pytest.fixture
def ai_down(monkeypatch):
    def boom(*args, **kwargs):
        raise AIServiceError("unavailable")

    monkeypatch.setattr("apps.ai.services.get_forecast", boom)
    monkeypatch.setattr("apps.ai.services.get_technical", boom)


def _linked_article(instrument, title, label):
    article = NewsArticle.objects.create(
        source="test",
        source_url=f"https://example.com/{title}".replace(" ", "-"),
        url_hash=title.replace(" ", "-"),
        simhash=0,
        title=title,
        body="body",
        published_at=timezone.now(),
        impact_score=75,
    )
    NewsEntity.objects.create(
        article=article,
        entity_type="org",
        entity_text=instrument.symbol,
        linked_kind="instrument",
        linked_id=instrument.id,
    )
    NewsSentiment.objects.create(article=article, label=label, score=-0.7, confidence=0.9)
    return article


def test_analysis_requires_auth(client):
    inst = InstrumentFactory()
    assert client.get(f"/api/v1/markets/instruments/{inst.symbol}/analysis/").status_code == 401


def test_analysis_unknown_symbol_404(client):
    client.force_authenticate(UserFactory())
    assert client.get("/api/v1/markets/instruments/NOPE/analysis/").status_code == 404


def test_analysis_fuses_forecast_technical_and_news(client, ai_up):
    client.force_authenticate(UserFactory())
    inst = InstrumentFactory()
    market_cache.set_quote(inst.id, {"price": 100.0, "change_percent": 1.0})
    _linked_article(inst, "Prices tumble on weak demand", "negative")

    data = client.get(f"/api/v1/markets/instruments/{inst.symbol}/analysis/").json()["data"]

    assert data["instrument"]["symbol"] == inst.symbol
    assert data["quote"]["price"] == 100.0
    assert "points" in data["history"]
    assert data["forecast"]["model"] == "linreg-v1"
    assert data["technical"]["signal"] == "buy"
    # News sentiment -> effect.
    assert data["news"][0]["effect"] == "bearish"
    assert data["news_effect"]["bias"] == "bearish"
    # Fused summary: forecast (110 > 100) + technical buy outweigh bearish news.
    assert data["ai_summary"]["bias"] == "bullish"
    assert data["ai_summary"]["target"] == 110.0
    assert data["ai_summary"]["target_change_pct"] == 10.0
    assert data["ai_summary"]["signals_considered"] == 3


def test_analysis_degrades_when_ai_unavailable(client, ai_down):
    client.force_authenticate(UserFactory())
    inst = InstrumentFactory()
    market_cache.set_quote(inst.id, {"price": 100.0, "change_percent": 1.0})
    _linked_article(inst, "Prices tumble", "negative")

    data = client.get(f"/api/v1/markets/instruments/{inst.symbol}/analysis/").json()["data"]

    # Structure intact; AI parts degrade to null but news still drives the view.
    assert data["forecast"] is None
    assert data["technical"] is None
    assert data["news_effect"]["bias"] == "bearish"
    assert data["ai_summary"]["bias"] == "bearish"


def test_analysis_neutral_when_no_signals(client, ai_down):
    client.force_authenticate(UserFactory())
    inst = InstrumentFactory()
    data = client.get(f"/api/v1/markets/instruments/{inst.symbol}/analysis/").json()["data"]
    assert data["news_effect"]["bias"] == "neutral"
    assert data["ai_summary"]["bias"] == "neutral"
    assert data["ai_summary"]["signals_considered"] == 0
