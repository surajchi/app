import pytest
from rest_framework.test import APIClient

from apps.rbac import services as rbac
from apps.rbac.constants import ROLE_FREE
from apps.users.models import User
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

ME = "/api/v1/users/me/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_me_requires_auth(client):
    assert client.get(ME).status_code == 401


def test_me_returns_user_with_roles(client):
    user = UserFactory(email="me@example.com")
    rbac.assign_role(user, ROLE_FREE)
    client.force_authenticate(user)
    resp = client.get(ME)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["email"] == "me@example.com"
    assert ROLE_FREE in data["roles"]


def test_me_patch_updates_name_and_phone(client):
    user = UserFactory()
    client.force_authenticate(user)
    resp = client.patch(ME, {"full_name": "New Name", "phone": "+919812345678"}, format="json")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["full_name"] == "New Name"
    assert data["phone"] == "+919812345678"
    assert "roles" in data  # full representation returned


def test_me_delete_soft_deletes(client):
    user = UserFactory()
    client.force_authenticate(user)
    resp = client.delete(ME)
    assert resp.status_code == 204
    user.refresh_from_db()
    assert user.is_active is False
    assert user.status == User.Status.DELETED
