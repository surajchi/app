import pytest
from rest_framework.test import APIClient

from apps.markets import cache as market_cache
from apps.markets.tests.factories import InstrumentFactory
from apps.users.tests.factories import UserFactory
from apps.watchlists.models import Watchlist, WatchlistItem

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _auth(client, user=None):
    user = user or UserFactory()
    client.force_authenticate(user)
    return user


def test_requires_auth(client):
    assert client.get("/api/v1/watchlists/").status_code == 401


def test_create_and_list(client):
    user = _auth(client)
    resp = client.post("/api/v1/watchlists/", {"name": "Majors"}, format="json")
    assert resp.status_code == 201, resp.content
    assert Watchlist.objects.filter(user=user, name="Majors").exists()
    assert len(client.get("/api/v1/watchlists/").json()["data"]) == 1


def test_setting_default_unsets_others(client):
    user = _auth(client)
    a = Watchlist.objects.create(user=user, name="A", is_default=True)
    resp = client.post("/api/v1/watchlists/", {"name": "B", "is_default": True}, format="json")
    assert resp.status_code == 201
    a.refresh_from_db()
    assert a.is_default is False


def test_are_user_scoped(client):
    owner = UserFactory()
    Watchlist.objects.create(user=owner, name="Owner list")
    _auth(client)  # a different user
    assert client.get("/api/v1/watchlists/").json()["data"] == []


def test_add_item_with_quote(client):
    user = _auth(client)
    wl = Watchlist.objects.create(user=user, name="Majors")
    inst = InstrumentFactory()
    market_cache.set_quote(inst.id, {"price": 100.0, "change_percent": 1.5})
    resp = client.post(
        f"/api/v1/watchlists/{wl.id}/items/",
        {"instrument_id": str(inst.id), "note": "watch"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()["data"]
    assert body["instrument"]["symbol"] == inst.symbol
    assert body["quote"]["price"] == 100.0


def test_add_duplicate_item_conflicts(client):
    user = _auth(client)
    wl = Watchlist.objects.create(user=user, name="Majors")
    inst = InstrumentFactory()
    payload = {"instrument_id": str(inst.id)}
    assert (
        client.post(f"/api/v1/watchlists/{wl.id}/items/", payload, format="json").status_code == 201
    )
    assert (
        client.post(f"/api/v1/watchlists/{wl.id}/items/", payload, format="json").status_code == 409
    )


def test_remove_item(client):
    user = _auth(client)
    wl = Watchlist.objects.create(user=user, name="Majors")
    item = WatchlistItem.objects.create(watchlist=wl, instrument=InstrumentFactory())
    resp = client.delete(f"/api/v1/watchlists/{wl.id}/items/{item.id}/")
    assert resp.status_code == 204
    assert not WatchlistItem.objects.filter(id=item.id).exists()


def test_reorder(client):
    user = _auth(client)
    wl = Watchlist.objects.create(user=user, name="Majors")
    i1 = WatchlistItem.objects.create(watchlist=wl, instrument=InstrumentFactory(), position=1)
    i2 = WatchlistItem.objects.create(watchlist=wl, instrument=InstrumentFactory(), position=2)
    resp = client.post(
        f"/api/v1/watchlists/{wl.id}/reorder/",
        {"item_ids": [str(i2.id), str(i1.id)]},
        format="json",
    )
    assert resp.status_code == 200
    i1.refresh_from_db()
    i2.refresh_from_db()
    assert (i2.position, i1.position) == (1, 2)


def test_detail_includes_items(client):
    user = _auth(client)
    wl = Watchlist.objects.create(user=user, name="Majors")
    WatchlistItem.objects.create(watchlist=wl, instrument=InstrumentFactory())
    data = client.get(f"/api/v1/watchlists/{wl.id}/").json()["data"]
    assert data["item_count"] == 1
    assert len(data["items"]) == 1


def test_cannot_access_others_watchlist(client):
    owner = UserFactory()
    wl = Watchlist.objects.create(user=owner, name="Owner")
    _auth(client)
    assert client.get(f"/api/v1/watchlists/{wl.id}/").status_code == 404
