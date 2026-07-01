"""Celery ingestion task for the news pipeline."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger("finpulse")


@shared_task(name="apps.news.tasks.ingest_news")
def ingest_news() -> int:
    """Fetch from the active provider and run each article through the pipeline."""
    from apps.news.pipeline import process
    from integrations.news.registry import get_news_provider
    from realtime.publish import publish_news

    provider = get_news_provider()
    created = 0
    for raw in provider.fetch():
        try:
            article = process(raw)
        except Exception:  # noqa: BLE001 - one bad article must not stop the sweep
            logger.exception("news.process_failed", extra={"url": raw.url})
            continue
        if article is None:
            continue
        created += 1
        if article.is_breaking:
            publish_news(
                {
                    "id": str(article.id),
                    "title": article.title,
                    "category": article.category.slug if article.category_id else None,
                    "impact_score": article.impact_score,
                    "published_at": article.published_at.isoformat(),
                },
                category=article.category.slug if article.category_id else None,
            )
    logger.info("news.ingested", extra={"count": created})
    return created
