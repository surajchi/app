"""Deterministic economic-calendar generator + query helpers.

Free and offline: macro releases (CPI, NFP, rate decisions, GDP, PMI, …) are
generated from fixed templates with deterministic, hash-derived values so the
calendar and the daily/weekly brief work without any external data source.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from datetime import datetime, time, timedelta

from django.db.models import QuerySet
from django.utils import timezone

from apps.econcalendar.models import EconomicEvent

_CURRENCY_TIME: dict[str, tuple[int, int]] = {
    "USD": (12, 30),
    "EUR": (9, 0),
    "GBP": (6, 0),
    "JPY": (23, 50),
    "INR": (6, 0),
}
_CURRENCY_COUNTRY = {"USD": "US", "EUR": "EU", "GBP": "GB", "JPY": "JP", "INR": "IN"}

# title, category, importance, weekday (0=Mon), currencies
_TEMPLATES: list[dict] = [
    {
        "t": "Manufacturing PMI",
        "c": "growth",
        "imp": "medium",
        "wd": 0,
        "cur": ["USD", "EUR", "GBP"],
    },
    {"t": "Retail Sales m/m", "c": "consumer", "imp": "medium", "wd": 1, "cur": ["USD", "GBP"]},
    {"t": "CPI y/y", "c": "inflation", "imp": "high", "wd": 2, "cur": ["USD", "EUR", "GBP"]},
    {"t": "Interest Rate Decision", "c": "rates", "imp": "high", "wd": 2, "cur": ["USD", "EUR"]},
    {"t": "GDP q/q", "c": "growth", "imp": "high", "wd": 3, "cur": ["USD", "EUR"]},
    {"t": "Initial Jobless Claims", "c": "employment", "imp": "medium", "wd": 3, "cur": ["USD"]},
    {"t": "Non-Farm Payrolls", "c": "employment", "imp": "high", "wd": 4, "cur": ["USD"]},
    {"t": "Unemployment Rate", "c": "employment", "imp": "medium", "wd": 4, "cur": ["USD", "EUR"]},
]


def _hash(*parts: str) -> int:
    return int(hashlib.sha256(":".join(parts).encode()).hexdigest(), 16)


def _values(tpl: dict, currency: str, day: dt.date, event_time: datetime) -> dict[str, str]:
    seed = f"{day.isoformat()}:{tpl['t']}:{currency}"
    h = _hash(seed)
    if tpl["t"] == "Non-Farm Payrolls":
        unit, prev, fore = "K", f"{120 + h % 160}K", f"{120 + (h >> 8) % 160}K"
    elif tpl["c"] == "employment" and "Claims" in tpl["t"]:
        unit, prev, fore = "K", f"{200 + h % 60}K", f"{200 + (h >> 8) % 60}K"
    else:
        unit = "%"
        prev = f"{1.0 + (h % 45) / 10:.1f}%"
        fore = f"{1.0 + ((h >> 8) % 45) / 10:.1f}%"
    actual = ""
    if event_time <= timezone.now():
        actual = (
            f"{120 + (h >> 16) % 180}K"
            if unit == "K"
            else f"{1.0 + ((h >> 16) % 45) / 10:.1f}%"
        )
    return {"unit": unit, "previous": prev, "forecast": fore, "actual": actual}


def ensure_events(days: int = 14) -> int:
    """Upsert generated events for the next ``days`` days. Returns count created."""
    today = timezone.now().date()
    created = 0
    for offset in range(days):
        day = today + timedelta(days=offset)
        for tpl in _TEMPLATES:
            if tpl["wd"] != day.weekday():
                continue
            for currency in tpl["cur"]:
                # Thin out medium/low events so the calendar isn't uniform.
                if tpl["imp"] != "high" and _hash(str(day), tpl["t"], currency) % 3 == 0:
                    continue
                hour, minute = _CURRENCY_TIME.get(currency, (12, 0))
                event_time = datetime.combine(day, time(hour, minute), tzinfo=dt.UTC)
                values = _values(tpl, currency, day, event_time)
                _, was_created = EconomicEvent.objects.update_or_create(
                    currency=currency,
                    title=tpl["t"],
                    event_time=event_time,
                    defaults={
                        "country": _CURRENCY_COUNTRY.get(currency, ""),
                        "importance": tpl["imp"],
                        "category": tpl["c"],
                        "source": "generated",
                        **values,
                    },
                )
                created += int(was_created)
    return created


def events_between(start: datetime, end: datetime) -> QuerySet[EconomicEvent]:
    return EconomicEvent.objects.filter(event_time__gte=start, event_time__lt=end)


def week_bounds(ref: datetime | None = None) -> tuple[datetime, datetime]:
    now = ref or timezone.now()
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return monday, monday + timedelta(days=7)


def this_week_events(high_only: bool = False) -> QuerySet[EconomicEvent]:
    start, end = week_bounds()
    qs = events_between(start, end)
    if high_only:
        qs = qs.filter(importance="high")
    return qs
