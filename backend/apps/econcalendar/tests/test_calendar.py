from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.econcalendar.models import EconomicEvent
from apps.econcalendar.services import ensure_events

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_ensure_events_creates_and_is_idempotent():
    first = ensure_events(days=14)
    assert first > 0
    assert EconomicEvent.objects.count() == first
    # Second run upserts the same events -> nothing new created.
    assert ensure_events(days=14) == 0


def test_calendar_list_returns_window(client):
    ensure_events(days=14)
    now = timezone.now()
    resp = client.get(
        "/api/v1/calendar/",
        {"from": now.isoformat(), "to": (now + timedelta(days=14)).isoformat()},
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]) > 0


def test_calendar_importance_filter(client):
    ensure_events(days=14)
    now = timezone.now()
    resp = client.get(
        "/api/v1/calendar/",
        {
            "from": now.isoformat(),
            "to": (now + timedelta(days=14)).isoformat(),
            "importance": "high",
        },
    )
    data = resp.json()["data"]
    assert data  # there are high-impact templates every week
    assert all(e["importance"] == "high" for e in data)


def test_calendar_week_endpoint(client):
    ensure_events(days=14)
    resp = client.get("/api/v1/calendar/week/")
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert "start" in body and "end" in body
    assert isinstance(body["events"], list)
