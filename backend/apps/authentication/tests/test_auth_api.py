import pytest
from rest_framework.test import APIClient

from apps.users.models import User
from apps.users.tests.factories import DEFAULT_TEST_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register/"
LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/refresh/"
LOGOUT = "/api/v1/auth/logout/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_register_creates_user_and_returns_tokens(client):
    resp = client.post(
        REGISTER,
        {"email": "new@example.com", "full_name": "New User", "password": "Str0ngPass!23"},
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["access"] and body["data"]["refresh"]
    assert body["data"]["user"]["email"] == "new@example.com"
    assert User.objects.filter(email="new@example.com").exists()


def test_register_rejects_weak_password(client):
    resp = client.post(
        REGISTER,
        {"email": "weak@example.com", "full_name": "Weak", "password": "123"},
        format="json",
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["details"] is not None


def test_register_rejects_duplicate_email(client):
    UserFactory(email="dup@example.com")
    resp = client.post(
        REGISTER,
        {"email": "dup@example.com", "full_name": "Dup", "password": "Str0ngPass!23"},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["success"] is False


def test_login_returns_tokens_and_user(client):
    UserFactory(email="login@example.com")
    resp = client.post(
        LOGIN, {"email": "login@example.com", "password": DEFAULT_TEST_PASSWORD}, format="json"
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["access"] and data["refresh"]
    assert data["expires_in"] > 0
    assert data["user"]["email"] == "login@example.com"


def test_login_is_case_insensitive_on_email(client):
    UserFactory(email="case@example.com")
    resp = client.post(
        LOGIN, {"email": "CASE@example.com", "password": DEFAULT_TEST_PASSWORD}, format="json"
    )
    assert resp.status_code == 200


def test_login_wrong_password_fails(client):
    UserFactory(email="wrong@example.com")
    resp = client.post(LOGIN, {"email": "wrong@example.com", "password": "nope"}, format="json")
    assert resp.status_code == 401
    assert resp.json()["success"] is False


def test_refresh_returns_new_access(client):
    UserFactory(email="refresh@example.com")
    login = client.post(
        LOGIN, {"email": "refresh@example.com", "password": DEFAULT_TEST_PASSWORD}, format="json"
    )
    refresh_token = login.json()["data"]["refresh"]
    resp = client.post(REFRESH, {"refresh": refresh_token}, format="json")
    assert resp.status_code == 200
    assert resp.json()["data"]["access"]


def test_logout_blacklists_refresh_token(client):
    UserFactory(email="logout@example.com")
    login = client.post(
        LOGIN, {"email": "logout@example.com", "password": DEFAULT_TEST_PASSWORD}, format="json"
    )
    data = login.json()["data"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")

    resp = client.post(LOGOUT, {"refresh": data["refresh"]}, format="json")
    assert resp.status_code == 205

    # The blacklisted refresh token can no longer be used.
    resp2 = client.post(REFRESH, {"refresh": data["refresh"]}, format="json")
    assert resp2.status_code == 401


def test_logout_requires_authentication(client):
    resp = client.post(LOGOUT, {"refresh": "whatever"}, format="json")
    assert resp.status_code == 401


def test_liveness_probe(client):
    resp = client.get("/healthz/")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ok"


def test_readiness_probe(client):
    resp = client.get("/readyz/")
    assert resp.status_code == 200
    assert resp.json()["data"]["checks"]["database"] == "ok"
