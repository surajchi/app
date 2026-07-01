"""OpenSearch index + queries for news (self-hosted; no external cost)."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from django.conf import settings

if TYPE_CHECKING:
    from apps.news.models import NewsArticle

logger = logging.getLogger("finpulse")

NEWS_INDEX = "news"

MAPPING: dict[str, Any] = {
    "properties": {
        "title": {"type": "text"},
        "body": {"type": "text"},
        "summary": {"type": "text"},
        "source": {"type": "keyword"},
        "category": {"type": "keyword"},
        "symbols": {"type": "keyword"},
        "sentiment": {"type": "keyword"},
        "impact_score": {"type": "integer"},
        "is_breaking": {"type": "boolean"},
        "published_at": {"type": "date"},
    }
}


@lru_cache(maxsize=1)
def get_client() -> Any:
    from opensearchpy import OpenSearch

    return OpenSearch(
        hosts=[settings.OPENSEARCH_URL],
        http_compress=True,
        timeout=5,
        max_retries=2,
        retry_on_timeout=True,
    )


def ensure_index(client: Any | None = None) -> None:
    client = client or get_client()
    if not client.indices.exists(index=NEWS_INDEX):
        client.indices.create(index=NEWS_INDEX, body={"mappings": MAPPING})


def to_document(article: NewsArticle) -> dict[str, Any]:
    symbols = [e.entity_text for e in article.entities.all() if e.linked_kind == "instrument"]
    sentiment = article.sentiment.label if hasattr(article, "sentiment") else ""
    return {
        "title": article.title,
        "body": article.body,
        "summary": article.summary,
        "source": article.source,
        "category": article.category.slug if article.category_id else "",
        "symbols": symbols,
        "sentiment": sentiment,
        "impact_score": article.impact_score,
        "is_breaking": article.is_breaking,
        "published_at": article.published_at.isoformat(),
    }


def index_article(article: NewsArticle) -> None:
    client = get_client()
    ensure_index(client)
    client.index(index=NEWS_INDEX, id=str(article.id), body=to_document(article))


def safe_index_article(article: NewsArticle) -> None:
    """Index best-effort; never let a search outage break ingestion."""
    try:
        index_article(article)
    except Exception:  # noqa: BLE001
        logger.exception("search.index_failed", extra={"article": str(article.id)})


def delete_article(article_id: str) -> None:
    try:
        get_client().delete(index=NEWS_INDEX, id=str(article_id), ignore=[404])
    except Exception:  # noqa: BLE001
        logger.exception("search.delete_failed", extra={"article": str(article_id)})


def search_news(query: str, category: str | None = None, size: int = 30) -> list[str]:
    """Return article ids ranked by relevance (raises if OpenSearch is down)."""
    must: list[dict[str, Any]] = (
        [{"multi_match": {"query": query, "fields": ["title^3", "summary^2", "symbols^2", "body"]}}]
        if query
        else [{"match_all": {}}]
    )
    filters: list[dict[str, Any]] = []
    if category:
        filters.append({"term": {"category": category}})
    body = {
        "size": size,
        "query": {"bool": {"must": must, "filter": filters}},
        "sort": ["_score", {"published_at": "desc"}],
    }
    result = get_client().search(index=NEWS_INDEX, body=body)
    return [hit["_id"] for hit in result["hits"]["hits"]]


def reindex_all() -> int:
    from apps.news.models import NewsArticle

    client = get_client()
    if client.indices.exists(index=NEWS_INDEX):
        client.indices.delete(index=NEWS_INDEX)
    ensure_index(client)
    count = 0
    for article in (
        NewsArticle.objects.select_related("category", "sentiment")
        .prefetch_related("entities")
        .iterator(chunk_size=500)
    ):
        client.index(index=NEWS_INDEX, id=str(article.id), body=to_document(article))
        count += 1
    client.indices.refresh(index=NEWS_INDEX)
    return count
