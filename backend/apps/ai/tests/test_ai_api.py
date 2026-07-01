from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.ai.client import AIServiceError
from apps.ai.models import AIPrediction
from apps.markets.tests.factories import InstrumentFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

FORECAST_RESULT = {
    "points": [{"step": 1, "mean": 100.0, "low": 95.0, "high": 105.0}],
    "confidence": 0.7,
    "model": "linreg-v1",
}
TECH_RESULT = {"indicators": {"rsi": 55.0}, "signal": "hold", "strength": 0.33, "model": "ta-v1"}


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_forecast_requires_auth(client):
    InstrumentFactory(symbol="AAPL")
    assert client.get("/api/v1/ai/forecast/AAPL/").status_code == 401


def test_forecast_ok_persists_prediction(client):
    instrument = InstrumentFactory(symbol="AAPL")
    client.force_authenticate(UserFactory())
    with patch("apps.ai.client.forecast", return_value=FORECAST_RESULT) as mocked:
        resp = client.get("/api/v1/ai/forecast/AAPL/?horizon=5")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["confidence"] == 0.7
    assert data["symbol"] == "AAPL"
    assert data["horizon"] == "5d"
    assert "disclaimer" in data
    mocked.assert_called_once()
    assert (
        AIPrediction.objects.filter(instrument=instrument, prediction_type="price_forecast").count()
        == 1
    )


def test_forecast_unknown_symbol_404(client):
    client.force_authenticate(UserFactory())
    assert client.get("/api/v1/ai/forecast/NOPE/").status_code == 404


def test_forecast_service_unavailable_503(client):
    InstrumentFactory(symbol="MSFT")
    client.force_authenticate(UserFactory())
    with patch("apps.ai.client.forecast", side_effect=AIServiceError("down")):
        resp = client.get("/api/v1/ai/forecast/MSFT/")
    assert resp.status_code == 503
    assert resp.json()["success"] is False


def test_technical_ok(client):
    instrument = InstrumentFactory(symbol="TSLA")
    client.force_authenticate(UserFactory())
    with patch("apps.ai.client.technical", return_value=TECH_RESULT):
        resp = client.get("/api/v1/ai/technical/TSLA/")
    assert resp.status_code == 200
    assert resp.json()["data"]["signal"] == "hold"
    assert (
        AIPrediction.objects.filter(instrument=instrument, prediction_type="technical").count() == 1
    )
