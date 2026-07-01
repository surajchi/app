"""Resolve the active news provider (defaults to synthetic)."""

from __future__ import annotations

from django.conf import settings

from integrations.news.base import NewsProvider
from integrations.news.rss import RSSNewsProvider
from integrations.news.synthetic import SyntheticNewsProvider

_PROVIDERS: dict[str, type] = {
    "synthetic": SyntheticNewsProvider,
    "rss": RSSNewsProvider,
}


def get_news_provider(name: str | None = None) -> NewsProvider:
    name = name or getattr(settings, "NEWS_PROVIDER", "synthetic")
    provider_cls = _PROVIDERS.get(str(name), SyntheticNewsProvider)
    return provider_cls()
