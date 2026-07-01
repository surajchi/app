from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.markets import cache as market_cache
from apps.markets.tests.factories import InstrumentFactory
from apps.portfolios.models import Portfolio
from apps.portfolios.services import apply_transaction
from apps.users.tests.factories import UserFactory
from apps.watchlists.models import Watchlist, WatchlistItem

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_requires_auth(client):
    assert client.get("/api/v1/dashboard/").status_code == 401


def test_empty_dashboard_ok(client):
    user = UserFactory()
    client.force_authenticate(user)
    data = client.get("/api/v1/dashboard/").json()["data"]
    assert data["portfolio"] is None
    assert data["watchlist"] is None
    assert data["alerts"] == []
    assert "gainers" in data["movers"]


def test_dashboard_aggregates_domains(client):
    user = UserFactory()
    client.force_authenticate(user)

    inst = InstrumentFactory()
    market_cache.set_quote(inst.id, {"price": 120.0, "change_percent": 2.0})

    portfolio = Portfolio.objects.create(user=user, name="Main", is_default=True)
    apply_transaction(
        portfolio=portfolio,
        instrument=inst,
        type="buy",
        quantity=Decimal("10"),
        price=Decimal("100"),
    )

    watchlist = Watchlist.objects.create(user=user, name="Majors", is_default=True)
    WatchlistItem.objects.create(watchlist=watchlist, instrument=inst)

    data = client.get("/api/v1/dashboard/").json()["data"]
    assert data["portfolio"]["totals"]["market_value"] == 1200.0
    assert data["watchlist"]["name"] == "Majors"
    assert len(data["watchlist"]["items"]) == 1
    assert data["watchlist"]["items"][0]["quote"]["price"] == 120.0
