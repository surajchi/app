import datetime as dt

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.ai.models import Recommendation
from apps.markets.models import PriceBar
from apps.markets.tests.factories import InstrumentFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def _bars(instrument, start: float, step: float):
    base = timezone.now() - dt.timedelta(days=25)
    price = start
    for i in range(22):
        PriceBar.objects.create(
            instrument=instrument,
            interval="1d",
            ts=base + dt.timedelta(days=i),
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1000,
        )
        price += step


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_recommendations_requires_auth(client):
    assert client.get("/api/v1/ai/recommendations/").status_code == 401


def test_recommendations_rank_and_persist(client):
    up = InstrumentFactory(symbol="UP")
    down = InstrumentFactory(symbol="DN")
    _bars(up, 100.0, 2.0)  # rising -> positive momentum
    _bars(down, 100.0, -2.0)  # falling -> negative momentum

    user = UserFactory()
    client.force_authenticate(user)
    resp = client.get("/api/v1/ai/recommendations/?limit=5")
    assert resp.status_code == 200

    results = resp.json()["data"]["results"]
    symbols = [r["symbol"] for r in results]
    assert symbols.index("UP") < symbols.index("DN")
    assert results[0]["type"] == "buy_idea"
    assert Recommendation.objects.filter(user=user).count() == len(results)


def test_models_catalog(client):
    resp = client.get("/api/v1/ai/models/")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()["data"]["models"]]
    assert "forecast" in names
    assert "recommendations" in names
