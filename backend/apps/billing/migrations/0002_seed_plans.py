"""Seed the default subscription plans (idempotent)."""

from __future__ import annotations

from django.db import migrations

PLANS = [
    {
        "code": "free",
        "name": "Free",
        "description": "Get started with the essentials.",
        "price_cents": 0,
        "interval": "month",
        "trial_days": 0,
        "tier": 0,
        "role_name": "",
        "features": {
            "max_watchlists": 1,
            "max_watchlist_items": 20,
            "max_alerts": 5,
            "ai_requests_per_day": 10,
            "realtime": False,
            "priority_support": False,
        },
    },
    {
        "code": "premium",
        "name": "Premium",
        "description": "For active traders who need more.",
        "price_cents": 999,
        "interval": "month",
        "trial_days": 14,
        "tier": 1,
        "role_name": "premium",
        "features": {
            "max_watchlists": 5,
            "max_watchlist_items": 100,
            "max_alerts": 50,
            "ai_requests_per_day": 200,
            "realtime": True,
            "priority_support": False,
        },
    },
    {
        "code": "pro",
        "name": "Pro",
        "description": "Maximum limits and priority support.",
        "price_cents": 2999,
        "interval": "month",
        "trial_days": 14,
        "tier": 2,
        "role_name": "premium",
        "features": {
            "max_watchlists": 50,
            "max_watchlist_items": 1000,
            "max_alerts": 500,
            "ai_requests_per_day": 2000,
            "realtime": True,
            "priority_support": True,
        },
    },
]


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    for data in PLANS:
        Plan.objects.update_or_create(code=data["code"], defaults=data)


def unseed_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(code__in=[p["code"] for p in PLANS]).delete()


class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]

    operations = [migrations.RunPython(seed_plans, unseed_plans)]
