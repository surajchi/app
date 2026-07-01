"""Platform overview metrics aggregated across domains for the admin console."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import UserSession
from apps.ai.models import AIPrediction, Recommendation
from apps.alerts.models import Alert, AlertRule
from apps.markets.models import DataProviderStatus, Instrument
from apps.news.models import NewsArticle
from apps.notifications.constants import DeliveryStatus
from apps.notifications.models import Notification, NotificationDelivery
from apps.users.models import User


def build_overview() -> dict[str, Any]:
    now = timezone.now()
    day_ago = now - timedelta(days=1)

    active_sessions = UserSession.objects.filter(revoked_at__isnull=True).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )

    return {
        "users": {
            "total": User.objects.count(),
            "active": User.objects.filter(is_active=True).count(),
            "staff": User.objects.filter(is_staff=True).count(),
            "new_24h": User.objects.filter(created_at__gte=day_ago).count(),
        },
        "sessions": {"active": active_sessions.count()},
        "notifications": {
            "total": Notification.objects.count(),
            "delivered": NotificationDelivery.objects.filter(
                status=DeliveryStatus.DELIVERED
            ).count(),
        },
        "alerts": {
            "rules_active": AlertRule.objects.filter(is_active=True).count(),
            "fired_total": Alert.objects.count(),
        },
        "news": {
            "total": NewsArticle.objects.count(),
            "breaking": NewsArticle.objects.filter(is_breaking=True).count(),
            "new_24h": NewsArticle.objects.filter(published_at__gte=day_ago).count(),
        },
        "markets": {
            "instruments": Instrument.objects.filter(is_active=True).count(),
            "providers_down": DataProviderStatus.objects.filter(
                status=DataProviderStatus.Status.DOWN
            ).count(),
        },
        "ai": {
            "predictions": AIPrediction.objects.count(),
            "recommendations": Recommendation.objects.count(),
        },
    }
