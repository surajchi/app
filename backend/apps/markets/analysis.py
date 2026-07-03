"""Composite instrument analysis: fuse price history, AI forecast, technical
signals, and related-news sentiment into a single 'what could this do' view.

Everything degrades gracefully — if the AI service is unavailable the endpoint
still returns quote, history, and news so the detail screen stays useful.
"""

from __future__ import annotations

from typing import Any

from apps.markets import services
from apps.markets.models import Instrument

_CHART_POINTS = 90
_NEWS_LIMIT = 8

_LABEL_TO_EFFECT = {"positive": "bullish", "negative": "bearish", "neutral": "neutral"}


def _news_for(instrument: Instrument) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from apps.news.constants import ArticleStatus
    from apps.news.models import NewsArticle, NewsSentiment

    articles = list(
        NewsArticle.objects.filter(
            status=ArticleStatus.PUBLISHED,
            entities__linked_kind="instrument",
            entities__linked_id=instrument.id,
        )
        .distinct()
        .order_by("-published_at")[:_NEWS_LIMIT]
    )
    labels = dict(
        NewsSentiment.objects.filter(article__in=articles).values_list("article_id", "label")
    )

    items: list[dict[str, Any]] = []
    counts = {"bullish": 0, "bearish": 0, "neutral": 0}
    for article in articles:
        label = labels.get(article.id, "neutral")
        effect = _LABEL_TO_EFFECT.get(label, "neutral")
        counts[effect] += 1
        items.append(
            {
                "id": str(article.id),
                "title": article.title,
                "source": article.source,
                "published_at": article.published_at.isoformat(),
                "impact_score": article.impact_score,
                "sentiment": label,
                "effect": effect,
            }
        )

    if counts["bullish"] > counts["bearish"]:
        bias = "bullish"
    elif counts["bearish"] > counts["bullish"]:
        bias = "bearish"
    else:
        bias = "neutral"

    total = len(items)
    note = (
        f"{counts['bullish']} bullish / {counts['bearish']} bearish across "
        f"{total} recent article{'s' if total != 1 else ''}."
        if total
        else "No recent instrument-specific news."
    )
    news_effect = {"bias": bias, **counts, "count": total, "note": note}
    return items, news_effect


def _summary(
    price: float | None,
    forecast: dict[str, Any] | None,
    technical: dict[str, Any] | None,
    news_bias: str,
) -> dict[str, Any]:
    votes: list[int] = []
    target: float | None = None

    points = (forecast or {}).get("points") or []
    if points:
        target = float(points[-1]["mean"])
        if price:
            votes.append(1 if target > price else -1 if target < price else 0)

    signal = (technical or {}).get("signal")
    if signal == "buy":
        votes.append(1)
    elif signal == "sell":
        votes.append(-1)

    if news_bias == "bullish":
        votes.append(1)
    elif news_bias == "bearish":
        votes.append(-1)

    score = sum(votes)
    bias = "bullish" if score > 0 else "bearish" if score < 0 else "neutral"

    strengths: list[float] = []
    if forecast:
        strengths.append(float(forecast.get("confidence", 0.0)))
    if technical:
        strengths.append(float(technical.get("strength", 0.0)))
    base = sum(strengths) / len(strengths) if strengths else 0.3
    agreement = abs(score) / len(votes) if votes else 0.0
    confidence = round(min(0.95, 0.4 * base + 0.6 * agreement) * 100)

    change_pct = None
    if target is not None and price:
        change_pct = round((target - price) / price * 100, 2)

    return {
        "bias": bias,
        "confidence": confidence,
        "target": round(target, 4) if target is not None else None,
        "target_change_pct": change_pct,
        "signals_considered": len(votes),
        "rationale": _rationale(bias, forecast, technical, news_bias),
    }


def _rationale(
    bias: str,
    forecast: dict[str, Any] | None,
    technical: dict[str, Any] | None,
    news_bias: str,
) -> str:
    parts: list[str] = []
    if forecast and forecast.get("points"):
        trend = "up" if bias == "bullish" else "down" if bias == "bearish" else "flat"
        parts.append(f"model forecast trends {trend}")
    if technical and technical.get("signal"):
        parts.append(f"technicals signal {technical['signal']}")
    if news_bias != "neutral":
        parts.append(f"recent news leans {news_bias}")
    if not parts:
        return "Not enough data for a confident read yet."
    return "Outlook is " + bias + " — " + ", ".join(parts) + ". Not financial advice."


def build_instrument_analysis(instrument: Instrument, *, horizon: int = 7) -> dict[str, Any]:
    from apps.ai import services as ai_services
    from apps.ai.client import AIServiceError
    from apps.markets.serializers import InstrumentSerializer

    quote = services.latest_quote(instrument)
    price = quote.get("price") if quote else None

    bars = services.history(instrument, "1d", limit=_CHART_POINTS)
    history_points = [{"ts": bar.ts.isoformat(), "close": float(bar.close)} for bar in bars]

    forecast: dict[str, Any] | None = None
    technical: dict[str, Any] | None = None
    try:
        forecast = ai_services.get_forecast(instrument, horizon)
    except AIServiceError:
        forecast = None
    try:
        technical = ai_services.get_technical(instrument)
    except AIServiceError:
        technical = None

    news, news_effect = _news_for(instrument)
    summary = _summary(price, forecast, technical, news_effect["bias"])

    return {
        "instrument": InstrumentSerializer(instrument).data,
        "quote": quote,
        "history": {"interval": "1d", "points": history_points},
        "forecast": forecast,
        "technical": technical,
        "news": news,
        "news_effect": news_effect,
        "ai_summary": summary,
        "disclaimer": "AI-generated analysis. Not financial advice.",
    }
