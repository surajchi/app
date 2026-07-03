import pytest
from rest_framework.test import APIClient

from apps.dashboard.tasks import send_daily_brief
from apps.econcalendar.models import EconomicEvent
from apps.notifications.models import Notification
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_brief_requires_auth(client):
    assert client.get("/api/v1/dashboard/brief/").status_code == 401


def test_brief_structure_and_populates_calendar(client):
    client.force_authenticate(UserFactory())
    data = client.get("/api/v1/dashboard/brief/").json()["data"]

    assert data["market_mood"] in {"bullish", "bearish", "neutral"}
    assert 0 <= data["sentiment_index"]["score"] <= 100
    assert data["sentiment_index"]["label"] in {
        "Extreme Fear",
        "Fear",
        "Neutral",
        "Greed",
        "Extreme Greed",
    }
    assert isinstance(data["summary"], str) and data["summary"]
    assert isinstance(data["top_news"], list)
    assert isinstance(data["week_ahead"], list)
    assert isinstance(data["gainers"], list)
    # build_brief lazily seeds the calendar when empty.
    assert EconomicEvent.objects.count() > 0


def test_daily_brief_task_notifies_active_users():
    UserFactory()
    UserFactory()
    sent = send_daily_brief()
    assert sent >= 2
    assert Notification.objects.filter(type="news", title="Your daily market brief").count() >= 2
