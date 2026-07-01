"""Deterministic synthetic news provider (runs without keys or network).

Emits finance headlines referencing seeded instrument symbols so the dedup,
sentiment, and entity-linking stages all exercise real logic. Articles are
bucketed by the hour: re-fetching within the same hour yields duplicates (to
exercise dedup); a new hour yields fresh articles.
"""

from __future__ import annotations

from django.utils import timezone

from integrations.news.base import RawArticle

# (symbol, title, body)
_TEMPLATES: list[tuple[str, str, str]] = [
    (
        "AAPL",
        "Apple shares surge as quarterly earnings beat estimates",
        "Apple reported record revenue and strong guidance, sending the stock higher in trading.",
    ),
    (
        "RELIANCE",
        "Reliance Industries slumps on weak quarterly guidance",
        "Reliance shares fell after the company issued a cautious outlook citing margin pressure.",
    ),
    (
        "BTCUSD",
        "Bitcoin rallies past key resistance amid risk-on mood",
        "Bitcoin jumped as traders turned bullish on crypto following supportive macro signals.",
    ),
    (
        "XAUUSD",
        "Gold gains as inflation fears lift safe-haven demand",
        "Gold prices rose as investors sought safety amid rising inflation and rate uncertainty.",
    ),
    (
        "NIFTY50",
        "Nifty 50 hits record high on broad market rally",
        "Indian equities rallied with the Nifty 50 index closing at an all-time high.",
    ),
    (
        "EURUSD",
        "US Dollar falls against the euro after dovish Fed remarks",
        "The dollar weakened versus the euro following dovish commentary from Fed officials.",
    ),
]


class SyntheticNewsProvider:
    name = "synthetic"

    def fetch(self) -> list[RawArticle]:
        now = timezone.now()
        bucket = now.strftime("%Y%m%d%H")
        articles: list[RawArticle] = []
        for index, (symbol, title, body) in enumerate(_TEMPLATES):
            articles.append(
                RawArticle(
                    source="synthetic",
                    url=f"https://news.example/synthetic/{bucket}/{index}-{symbol.lower()}",
                    title=title,
                    body=body,
                    published_at=now,
                    author="FinPulse Wire",
                )
            )
        return articles
