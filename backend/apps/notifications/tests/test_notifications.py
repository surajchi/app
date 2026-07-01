import pytest
from rest_framework.test import APIClient

from apps.notifications.services import create_notification, get_preferences
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


# --- service ----------------------------------------------------------------


def test_create_and_dispatch_delivers_free_channels():
    user = UserFactory()
    notification = create_notification(user=user, type="system", title="Hello", body="Body")
    assert notification is not None
    statuses = {d.channel: d.status for d in notification.deliveries.all()}
    assert statuses["in_app"] == "delivered"
    assert statuses["email"] == "delivered"


def test_unconfigured_channel_is_skipped():
    user = UserFactory()
    # alert default includes "push", which has no configured backend.
    notification = create_notification(user=user, type="alert", title="Alert")
    statuses = {d.channel: d.status for d in notification.deliveries.all()}
    assert statuses["in_app"] == "delivered"
    assert statuses["push"] == "skipped"


def test_marketing_suppressed_without_optin():
    user = UserFactory()
    assert create_notification(user=user, type="marketing", title="Promo") is None


def test_marketing_sent_with_optin():
    user = UserFactory()
    prefs = get_preferences(user)
    prefs.marketing_opt_in = True
    prefs.save()
    assert create_notification(user=user, type="marketing", title="Promo") is not None


def test_quiet_hours_limits_noncritical_to_in_app():
    user = UserFactory()
    prefs = get_preferences(user)
    prefs.quiet_hours = {"start": "00:00", "end": "23:59"}
    prefs.save()
    notification = create_notification(user=user, type="alert", title="A", priority="high")
    channels = {d.channel for d in notification.deliveries.all()}
    assert channels == {"in_app"}


def test_critical_bypasses_quiet_hours():
    user = UserFactory()
    prefs = get_preferences(user)
    prefs.quiet_hours = {"start": "00:00", "end": "23:59"}
    prefs.save()
    notification = create_notification(user=user, type="alert", title="A", priority="critical")
    channels = {d.channel for d in notification.deliveries.all()}
    assert "email" in channels


# --- API --------------------------------------------------------------------


def test_inbox_requires_auth(client):
    assert client.get("/api/v1/notifications/").status_code == 401


def test_inbox_list_and_unread_filter(client):
    user = UserFactory()
    create_notification(user=user, type="system", title="One")
    create_notification(user=user, type="system", title="Two")
    client.force_authenticate(user)
    assert len(client.get("/api/v1/notifications/").json()["data"]) == 2

    first_id = client.get("/api/v1/notifications/").json()["data"][0]["id"]
    client.post("/api/v1/notifications/read/", {"ids": [first_id]}, format="json")
    unread = client.get("/api/v1/notifications/?unread=true").json()["data"]
    assert len(unread) == 1


def test_mark_all_read(client):
    user = UserFactory()
    create_notification(user=user, type="system", title="One")
    create_notification(user=user, type="system", title="Two")
    client.force_authenticate(user)
    resp = client.post("/api/v1/notifications/read/", {"all": True}, format="json")
    assert resp.status_code == 200
    assert client.get("/api/v1/notifications/?unread=true").json()["data"] == []


def test_preferences_get_and_update(client):
    user = UserFactory()
    client.force_authenticate(user)
    assert client.get("/api/v1/notifications/preferences/").status_code == 200
    resp = client.put(
        "/api/v1/notifications/preferences/",
        {"channels": {"system": ["in_app"]}, "marketing_opt_in": True},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["marketing_opt_in"] is True


def test_device_register(client):
    user = UserFactory()
    client.force_authenticate(user)
    resp = client.post(
        "/api/v1/notifications/devices/register/",
        {"platform": "web", "push_token": "tok-123", "device_name": "Chrome"},
        format="json",
    )
    assert resp.status_code == 201
    assert user.devices.filter(push_token="tok-123").exists()


def test_test_endpoint_creates_notification(client):
    user = UserFactory()
    client.force_authenticate(user)
    resp = client.post("/api/v1/notifications/test/", format="json")
    assert resp.status_code == 201
    assert user.notifications.filter(title="Test notification").exists()
