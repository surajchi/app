from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.markets import cache as market_cache
from apps.markets.tests.factories import InstrumentFactory
from apps.portfolios.models import Holding, Portfolio
from apps.portfolios.services import (
    InsufficientHoldingError,
    apply_transaction,
    portfolio_valuation,
)
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


# --- service: holdings math -------------------------------------------------


def test_buy_sets_avg_cost_including_fee():
    user = UserFactory()
    p = Portfolio.objects.create(user=user, name="Main")
    inst = InstrumentFactory()
    apply_transaction(
        portfolio=p,
        instrument=inst,
        type="buy",
        quantity=Decimal("10"),
        price=Decimal("100"),
        fee=Decimal("5"),
    )
    h = Holding.objects.get(portfolio=p, instrument=inst)
    assert h.quantity == Decimal("10")
    assert h.avg_cost == Decimal("100.5")  # (10*100 + 5) / 10


def test_second_buy_weights_average():
    user = UserFactory()
    p = Portfolio.objects.create(user=user, name="Main")
    inst = InstrumentFactory()
    apply_transaction(
        portfolio=p, instrument=inst, type="buy", quantity=Decimal("10"), price=Decimal("100")
    )
    apply_transaction(
        portfolio=p, instrument=inst, type="buy", quantity=Decimal("10"), price=Decimal("110")
    )
    h = Holding.objects.get(portfolio=p, instrument=inst)
    assert h.quantity == Decimal("20")
    assert h.avg_cost == Decimal("105")  # (1000 + 1100) / 20


def test_sell_records_realized_pnl():
    user = UserFactory()
    p = Portfolio.objects.create(user=user, name="Main")
    inst = InstrumentFactory()
    apply_transaction(
        portfolio=p, instrument=inst, type="buy", quantity=Decimal("10"), price=Decimal("100")
    )
    apply_transaction(
        portfolio=p, instrument=inst, type="sell", quantity=Decimal("4"), price=Decimal("120")
    )
    h = Holding.objects.get(portfolio=p, instrument=inst)
    assert h.quantity == Decimal("6")
    assert h.realized_pnl == Decimal("80")  # 4 * (120 - 100)


def test_oversell_raises():
    user = UserFactory()
    p = Portfolio.objects.create(user=user, name="Main")
    inst = InstrumentFactory()
    apply_transaction(
        portfolio=p, instrument=inst, type="buy", quantity=Decimal("1"), price=Decimal("100")
    )
    with pytest.raises(InsufficientHoldingError):
        apply_transaction(
            portfolio=p, instrument=inst, type="sell", quantity=Decimal("2"), price=Decimal("120")
        )


def test_valuation_marks_to_market():
    user = UserFactory()
    p = Portfolio.objects.create(user=user, name="Main")
    inst = InstrumentFactory()
    apply_transaction(
        portfolio=p, instrument=inst, type="buy", quantity=Decimal("10"), price=Decimal("100")
    )
    market_cache.set_quote(inst.id, {"price": 120.0, "change_percent": 1.0})
    val = portfolio_valuation(p)
    assert val["totals"]["market_value"] == 1200.0
    assert val["totals"]["cost_basis"] == 1000.0
    assert val["totals"]["unrealized_pnl"] == 200.0
    assert val["positions"][0]["allocation_pct"] == 100.0


# --- API --------------------------------------------------------------------


def test_requires_auth(client):
    assert client.get("/api/v1/portfolios/").status_code == 401


def test_create_and_default(client):
    user = UserFactory()
    client.force_authenticate(user)
    a = Portfolio.objects.create(user=user, name="A", is_default=True)
    resp = client.post("/api/v1/portfolios/", {"name": "B", "is_default": True}, format="json")
    assert resp.status_code == 201
    a.refresh_from_db()
    assert a.is_default is False


def test_transaction_endpoint_updates_holding(client):
    user = UserFactory()
    client.force_authenticate(user)
    p = Portfolio.objects.create(user=user, name="Main")
    inst = InstrumentFactory()
    resp = client.post(
        f"/api/v1/portfolios/{p.id}/transactions/",
        {"instrument_id": str(inst.id), "type": "buy", "quantity": "5", "price": "50"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert Holding.objects.get(portfolio=p, instrument=inst).quantity == Decimal("5")


def test_oversell_endpoint_returns_400(client):
    user = UserFactory()
    client.force_authenticate(user)
    p = Portfolio.objects.create(user=user, name="Main")
    inst = InstrumentFactory()
    resp = client.post(
        f"/api/v1/portfolios/{p.id}/transactions/",
        {"instrument_id": str(inst.id), "type": "sell", "quantity": "5", "price": "50"},
        format="json",
    )
    assert resp.status_code == 400


def test_summary_endpoint(client):
    user = UserFactory()
    client.force_authenticate(user)
    p = Portfolio.objects.create(user=user, name="Main")
    inst = InstrumentFactory()
    apply_transaction(
        portfolio=p, instrument=inst, type="buy", quantity=Decimal("2"), price=Decimal("10")
    )
    market_cache.set_quote(inst.id, {"price": 15.0, "change_percent": 1.0})
    data = client.get(f"/api/v1/portfolios/{p.id}/summary/").json()["data"]
    assert data["totals"]["market_value"] == 30.0
    assert data["totals"]["unrealized_pnl"] == 10.0


def test_portfolios_user_scoped(client):
    owner = UserFactory()
    Portfolio.objects.create(user=owner, name="Owner")
    client.force_authenticate(UserFactory())
    assert client.get("/api/v1/portfolios/").json()["data"] == []
