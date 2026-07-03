"""Daily/weekly market brief: today's news + week-ahead events + AI narrative.

Surfaced even when the user has no alerts, via the dashboard card and a daily
notification.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone


def _narrative(mood: str, gainers: list[dict], events: list) -> str:
    parts = [f"Market mood looks {mood} based on the last 24h of news flow."]
    leaders = [
        f"{g['symbol']} ({g['change_percent']:+.2f}%)"
        for g in gainers[:3]
        if g.get("change_percent") is not None
    ]
    if leaders:
        parts.append("Leaders: " + ", ".join(leaders) + ".")
    names = [f"{e.currency} {e.title}" for e in events[:3]]
    if names:
        parts.append("Key events this week: " + "; ".join(names) + ".")
    return " ".join(parts)


def _sentiment_label(score: int) -> str:
    if score < 25:
        return "Extreme Fear"
    if score < 45:
        return "Fear"
    if score < 55:
        return "Neutral"
    if score < 75:
        return "Greed"
    return "Extreme Greed"


def build_brief() -> dict[str, Any]:
    from apps.econcalendar.serializers import EconomicEventSerializer
    from apps.econcalendar.services import ensure_events, this_week_events
    from apps.markets.services import market_breadth, movers
    from apps.news.constants import ArticleStatus
    from apps.news.models import NewsArticle, NewsSentiment

    now = timezone.now()
    day_ago = now - timedelta(days=1)

    articles = list(
        NewsArticle.objects.filter(
            status=ArticleStatus.PUBLISHED, published_at__gte=day_ago
        ).order_by("-impact_score", "-published_at")[:6]
    )
    if not articles:
        articles = list(
            NewsArticle.objects.filter(status=ArticleStatus.PUBLISHED).order_by("-published_at")[:6]
        )
    labels = dict(
        NewsSentiment.objects.filter(article__in=articles).values_list("article_id", "label")
    )
    positive = sum(1 for a in articles if labels.get(a.id) == "positive")
    negative = sum(1 for a in articles if labels.get(a.id) == "negative")
    mood = "bullish" if positive > negative else "bearish" if negative > positive else "neutral"
    top_news = [
        {
            "id": str(a.id),
            "title": a.title,
            "source": a.source,
            "impact_score": a.impact_score,
            "is_breaking": a.is_breaking,
            "published_at": a.published_at.isoformat(),
            "sentiment": labels.get(a.id, "neutral"),
        }
        for a in articles
    ]

    if not this_week_events().exists():
        ensure_events(days=14)
    upcoming = list(
        this_week_events(high_only=True).filter(event_time__gte=now).order_by("event_time")[:8]
    )
    if not upcoming:
        upcoming = list(this_week_events(high_only=True).order_by("event_time")[:8])
    week_ahead = EconomicEventSerializer(upcoming, many=True).data

    def _row(row: dict) -> dict:
        return {
            "symbol": row["instrument"].symbol,
            "name": row["instrument"].name,
            "change_percent": row["quote"].get("change_percent"),
        }

    gainers = [_row(r) for r in movers(kind="gainers", limit=3)]
    losers = [_row(r) for r in movers(kind="losers", limit=3)]

    # Fear & Greed style index: market breadth (50%) + news mood (30%) + momentum (20%).
    breadth = market_breadth()
    adv, dec = breadth["advancers"], breadth["decliners"]
    breadth_score = (adv / (adv + dec) * 100) if (adv + dec) else 50.0
    news_score = (positive / (positive + negative) * 100) if (positive + negative) else 50.0
    momentum_score = max(0.0, min(100.0, 50 + breadth["avg_change"] * 10))
    score = round(0.5 * breadth_score + 0.3 * news_score + 0.2 * momentum_score)
    sentiment_index = {
        "score": score,
        "label": _sentiment_label(score),
        "advancers": adv,
        "decliners": dec,
    }

    return {
        "generated_at": now.isoformat(),
        "market_mood": mood,
        "sentiment_index": sentiment_index,
        "summary": _narrative(mood, gainers, upcoming),
        "top_news": top_news,
        "week_ahead": week_ahead,
        "gainers": gainers,
        "losers": losers,
        "disclaimer": "AI-generated brief. Not financial advice.",
    }
