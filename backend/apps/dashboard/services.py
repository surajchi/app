"""Assemble the home dashboard payload from the Phase 3-7 domains."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from apps.alerts.serializers import AlertSerializer
from apps.markets.serializers import InstrumentSerializer
from apps.markets.services import movers
from apps.news.models import NewsArticle, NewsSentiment
from apps.portfolios.services import portfolio_valuation
from apps.watchlists.serializers import WatchlistDetailSerializer

if TYPE_CHECKING:
    from apps.users.models import User

_TOP_NEWS = 5
_RECENT_ALERTS = 5
_MOVERS = 5


def _top_news() -> list[dict[str, Any]]:
    articles = list(NewsArticle.objects.order_by("-impact_score", "-published_at")[:_TOP_NEWS])
    labels = dict(
        NewsSentiment.objects.filter(article__in=articles).values_list("article_id", "label")
    )
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "source": a.source,
            "impact_score": a.impact_score,
            "is_breaking": a.is_breaking,
            "published_at": a.published_at.isoformat(),
            "sentiment": labels.get(a.id),
        }
        for a in articles
    ]


def _movers(kind: str) -> list[dict[str, Any]]:
    return [
        {
            "instrument": InstrumentSerializer(row["instrument"]).data,
            "price": row["quote"].get("price"),
            "change_percent": row["quote"].get("change_percent"),
        }
        for row in movers(kind=kind, limit=_MOVERS)
    ]


def build_dashboard(user: User) -> dict[str, Any]:
    portfolios = user.portfolios.all()
    portfolio = portfolios.filter(is_default=True).first() or portfolios.first()

    watchlists = user.watchlists.prefetch_related("items__instrument__exchange")
    watchlist = watchlists.filter(is_default=True).first() or watchlists.first()

    recent_alerts = user.alerts.select_related("rule")[:_RECENT_ALERTS]

    return {
        "portfolio": portfolio_valuation(portfolio) if portfolio else None,
        "watchlist": (WatchlistDetailSerializer(watchlist).data if watchlist else None),
        "alerts": AlertSerializer(recent_alerts, many=True).data,
        "top_news": _top_news(),
        "movers": {"gainers": _movers("gainers"), "losers": _movers("losers")},
    }
