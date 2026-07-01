"""News ingestion pipeline: dedup -> NLP -> store.

    RawArticle -> canonical URL/dedup -> simhash near-dup -> categorize -> summarize
    -> sentiment -> entities + linking -> impact -> persist (article + sentiment + entities)
"""

from __future__ import annotations

import hashlib
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.db import IntegrityError

from apps.news import sentiment_backend
from apps.news.constants import DEFAULT_CATEGORIES, NEAR_DUPLICATE_HAMMING, ArticleStatus
from apps.news.models import NewsArticle, NewsCategory, NewsEntity, NewsSentiment
from apps.news.nlp import analyzers, entities
from integrations.news.base import RawArticle

_BREAKING_THRESHOLD = 70
_RECENT_WINDOW = 200


def canonical_url(url: str) -> str:
    parts = urlparse(url.strip())
    return urlunparse(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", "", "")
    )


def url_hash(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()


def _is_near_duplicate(value: int) -> bool:
    if not value:
        return False
    recent = NewsArticle.objects.order_by("-ingested_at").values_list("simhash", flat=True)[
        :_RECENT_WINDOW
    ]
    return any(
        other and analyzers.hamming(value, other) <= NEAR_DUPLICATE_HAMMING for other in recent
    )


def _category_for(slug: str) -> NewsCategory:
    category, _ = NewsCategory.objects.get_or_create(
        slug=slug, defaults={"name": DEFAULT_CATEGORIES.get(slug, slug.title())}
    )
    return category


def process(raw: RawArticle) -> NewsArticle | None:
    """Process one raw article. Returns the created article, or None if a duplicate."""
    digest = url_hash(raw.url)
    if NewsArticle.objects.filter(url_hash=digest).exists():
        return None

    text = f"{raw.title}. {raw.body}"
    fingerprint = analyzers.simhash(text)
    if _is_near_duplicate(fingerprint):
        return None

    sentiment = sentiment_backend.analyze_sentiment(text)
    extracted = entities.extract_entities(text)
    score = analyzers.impact_score(raw.source, float(sentiment["score"]), len(extracted))

    try:
        article = NewsArticle.objects.create(
            source=raw.source,
            source_url=raw.url,
            url_hash=digest,
            simhash=fingerprint,
            title=raw.title,
            body=raw.body,
            summary=analyzers.summarize(raw.title, raw.body),
            author=raw.author,
            image_url=raw.image_url,
            language=raw.language,
            published_at=raw.published_at,
            category=_category_for(analyzers.categorize(text)),
            impact_score=score,
            is_breaking=score >= _BREAKING_THRESHOLD,
            status=ArticleStatus.PUBLISHED,
        )
    except IntegrityError:
        return None  # lost a race on url_hash

    NewsSentiment.objects.create(article=article, **sentiment)
    NewsEntity.objects.bulk_create([NewsEntity(article=article, **entity) for entity in extracted])

    if getattr(settings, "SEARCH_ENABLED", False):
        from search.news_index import safe_index_article

        safe_index_article(article)
    return article
