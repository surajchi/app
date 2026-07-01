"""Recommendation engine: blend price momentum + recent news sentiment.

Free/heuristic and personalized-ready (keyed by user). Portfolio/watchlist
signals get folded in once Phase 7 lands.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

from django.core.cache import cache
from django.db.models import Avg
from django.utils import timezone

from apps.ai.models import Recommendation
from apps.markets.models import Instrument, PriceBar
from apps.news.models import NewsSentiment

if TYPE_CHECKING:
    from apps.users.models import User

_MOMENTUM_WINDOW = 20
_SENTIMENT_DAYS = 7
_UNIVERSE_CAP = 200


def _momentum(instrument: Instrument) -> float:
    closes = list(
        PriceBar.objects.filter(instrument=instrument, interval="1d")
        .order_by("-ts")
        .values_list("close", flat=True)[:_MOMENTUM_WINDOW]
    )
    if len(closes) < 2:
        return 0.0
    latest, oldest = float(closes[0]), float(closes[-1])
    if oldest == 0:
        return 0.0
    return max(-1.0, min(1.0, (latest - oldest) / oldest * 5))


def _sentiment(instrument: Instrument) -> float:
    since = timezone.now() - dt.timedelta(days=_SENTIMENT_DAYS)
    avg = NewsSentiment.objects.filter(
        article__entities__linked_kind="instrument",
        article__entities__linked_id=instrument.id,
        article__published_at__gte=since,
    ).aggregate(avg=Avg("score"))["avg"]
    return float(avg or 0.0)


def _rationale(momentum: float, sentiment: float) -> str:
    m = "positive" if momentum > 0.05 else "negative" if momentum < -0.05 else "flat"
    s = "bullish" if sentiment > 0.1 else "bearish" if sentiment < -0.1 else "neutral"
    return f"{m.capitalize()} price momentum with {s} news sentiment."


def generate(user: User, limit: int = 10) -> dict[str, Any]:
    key = f"ai:recs:{user.id}:{limit}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    scored = []
    for instrument in Instrument.objects.filter(is_active=True).select_related("exchange")[
        :_UNIVERSE_CAP
    ]:
        momentum = _momentum(instrument)
        sentiment = _sentiment(instrument)
        score = round(0.6 * momentum + 0.4 * sentiment, 4)
        scored.append((instrument, score, momentum, sentiment))

    scored.sort(key=lambda row: row[1], reverse=True)
    top = scored[:limit]

    Recommendation.objects.filter(user=user).delete()
    records = []
    for instrument, score, momentum, sentiment in top:
        rec_type = (
            Recommendation.Kind.BUY_IDEA
            if score > 0.15
            else Recommendation.Kind.RISK_WARNING if score < -0.15 else Recommendation.Kind.WATCH
        )
        records.append(
            Recommendation(
                user=user,
                instrument=instrument,
                rec_type=rec_type,
                score=score,
                confidence=round(min(1.0, abs(score) + 0.3), 2),
                rationale=_rationale(momentum, sentiment),
                model="rec-blend-v1",
            )
        )
    Recommendation.objects.bulk_create(records)

    results = [
        {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "asset_class": instrument.asset_class,
            "type": record.rec_type,
            "score": record.score,
            "confidence": record.confidence,
            "rationale": record.rationale,
        }
        for (instrument, _s, _m, _se), record in zip(top, records, strict=False)
    ]
    payload = {"model": "rec-blend-v1", "results": results, "disclaimer": "Not financial advice."}
    cache.set(key, payload, 300)
    return payload
