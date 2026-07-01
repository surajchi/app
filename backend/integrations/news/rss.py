"""Minimal RSS news provider (stdlib only, no API key).

Reads feed URLs from settings.NEWS_RSS_FEEDS. Network failures degrade to an
empty list so the ingest sweep never crashes.
"""

from __future__ import annotations

import datetime as dt
import logging
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from integrations.news.base import RawArticle

logger = logging.getLogger("finpulse")
_TIMEOUT = 10


class RSSNewsProvider:
    name = "rss"

    def fetch(self) -> list[RawArticle]:
        feeds: list[str] = list(getattr(settings, "NEWS_RSS_FEEDS", []))
        articles: list[RawArticle] = []
        for url in feeds:
            try:
                articles.extend(self._fetch_feed(url))
            except Exception:  # noqa: BLE001 - one bad feed must not stop ingestion
                logger.exception("news.rss_fetch_failed", extra={"feed": url})
        return articles

    def _fetch_feed(self, url: str) -> list[RawArticle]:
        request = Request(url, headers={"User-Agent": "FinPulse/1.0"})
        with urlopen(request, timeout=_TIMEOUT) as response:  # noqa: S310 - configured feeds
            root = ElementTree.fromstring(response.read())

        out: list[RawArticle] = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not title or not link:
                continue
            published = parse_datetime(item.findtext("pubDate") or "") or timezone.now()
            if published.tzinfo is None:
                published = published.replace(tzinfo=dt.UTC)
            out.append(
                RawArticle(
                    source="rss",
                    url=link,
                    title=title,
                    body=(item.findtext("description") or "").strip(),
                    published_at=published,
                )
            )
        return out
