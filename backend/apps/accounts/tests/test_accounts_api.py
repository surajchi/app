import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Device, LoginHistory, UserSession
from apps.users.tests.factories import DEFAULT_TEST_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/refresh/"
SESSIONS = "/api/v1/auth/sessions/"
PASSWORD_CHANGE = "/api/v1/auth/password/change/"
DEVICES = "/api/v1/profile/devices/"
ACTIVITY = "/api/v1/profile/activity/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _login(client, email, password=DEFAULT_TEST_PASSWORD, device=None):
    body: dict = {"email": email, "password": password}
    if device:
        body["device"] = device
    return client.post(LOGIN, body, format="json")


def test_login_records_session_and_history(client):
    user = UserFactory(email="sess@example.com")
    resp = _login(client, "sess@example.com")
    assert resp.status_code == 200
    assert UserSession.objects.filter(user=user, revoked_at__isnull=True).count() == 1
    assert LoginHistory.objects.filter(user=user, event="login", success=True).count() == 1


def test_login_with_device_payload_creates_device(client):
    user = UserFactory(email="dev@example.com")
    _login(client, "dev@example.com", device={"platform": "web", "device_name": "Chrome"})
    assert Device.objects.filter(user=user, platform="web").exists()
    session = UserSession.objects.get(user=user)
    assert session.device is not None


def test_failed_login_records_history(client):
    user = UserFactory(email="bad@example.com")
    resp = _login(client, "bad@example.com", password="wrong")
    assert resp.status_code == 401
    assert LoginHistory.objects.filter(user=user, event="failed", success=False).count() == 1


def test_list_sessions(client):
    UserFactory(email="list@example.com")
    login = _login(client, "list@example.com")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['data']['access']}")
    resp = client.get(SESSIONS)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


def test_revoke_session_blacklists_refresh(client):
    UserFactory(email="rev@example.com")
    login = _login(client, "rev@example.com")
    data = login.json()["data"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
    session_id = client.get(SESSIONS).json()["data"][0]["id"]

    resp = client.delete(f"{SESSIONS}{session_id}/")
    assert resp.status_code == 204

    # The revoked session's refresh token is now blacklisted.
    fresh = APIClient()
    assert fresh.post(REFRESH, {"refresh": data["refresh"]}, format="json").status_code == 401


def test_activity_lists_login_events(client):
    UserFactory(email="act@example.com")
    login = _login(client, "act@example.com")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['data']['access']}")
    resp = client.get(ACTIVITY)
    assert resp.status_code == 200
    events = [row["event"] for row in resp.json()["data"]]
    assert "login" in events


def test_password_change_success_and_wrong_current(client):
    user = UserFactory(email="pw@example.com")
    login = _login(client, "pw@example.com")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['data']['access']}")

    bad = client.post(
        PASSWORD_CHANGE,
        {"current_password": "nope", "new_password": "NewStr0ng!23"},
        format="json",
    )
    assert bad.status_code == 400

    ok = client.post(
        PASSWORD_CHANGE,
        {"current_password": DEFAULT_TEST_PASSWORD, "new_password": "NewStr0ng!23"},
        format="json",
    )
    assert ok.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NewStr0ng!23")


def test_list_devices_requires_auth(client):
    assert client.get(DEVICES).status_code == 401
