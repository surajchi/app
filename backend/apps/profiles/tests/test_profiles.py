import pytest
from rest_framework.test import APIClient

from apps.profiles.models import Profile
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

PROFILE = "/api/v1/profile/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_profile_auto_created_with_user():
    user = UserFactory()
    assert Profile.objects.filter(user=user).exists()


def test_get_profile_requires_auth(client):
    assert client.get(PROFILE).status_code == 401


def test_get_profile_returns_defaults(client):
    user = UserFactory()
    client.force_authenticate(user)
    resp = client.get(PROFILE)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["base_currency"] == "USD"
    assert data["experience_level"] == "beginner"


def test_patch_profile_updates_and_normalizes(client):
    user = UserFactory()
    client.force_authenticate(user)
    resp = client.patch(
        PROFILE,
        {
            "base_currency": "inr",
            "country": "in",
            "risk_appetite": "high",
            "timezone": "Asia/Kolkata",
        },
        format="json",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["base_currency"] == "INR"
    assert data["country"] == "IN"
    assert data["risk_appetite"] == "high"
