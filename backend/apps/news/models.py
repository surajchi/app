"""News domain models: categories, articles, sentiment, and extracted entities."""

from __future__ import annotations

import uuid

from django.db import models

from apps.news.constants import ArticleStatus, EntityType, Sentiment
from common.mixins import BaseModel, TimeStampedModel


class NewsCategory(BaseModel):
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=80)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )

    class Meta:
        db_table = "news_categories"
        ordering = ["slug"]
        verbose_name_plural = "news categories"

    def __str__(self) -> str:
        return self.slug


class NewsArticle(BaseModel):
    source = models.CharField(max_length=80)
    source_url = models.TextField()
    url_hash = models.CharField(max_length=64, unique=True)  # sha256 of canonical URL
    simhash = models.BigIntegerField(db_index=True, default=0)  # near-dup detection

    title = models.TextField()
    body = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    author = models.CharField(max_length=150, blank=True)
    image_url = models.URLField(blank=True)
    language = models.CharField(max_length=5, default="en")

    published_at = models.DateTimeField(db_index=True)
    ingested_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        NewsCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles"
    )

    impact_score = models.PositiveSmallIntegerField(default=0)  # 0..100
    is_breaking = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=ArticleStatus.choices, default=ArticleStatus.PUBLISHED
    )

    class Meta:
        db_table = "news"
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["-published_at"], name="news_published_idx"),
            models.Index(fields=["-impact_score"], name="news_impact_idx"),
        ]

    def __str__(self) -> str:
        return self.title[:80]


class NewsSentiment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.OneToOneField(NewsArticle, on_delete=models.CASCADE, related_name="sentiment")
    label = models.CharField(max_length=10, choices=Sentiment.choices)
    score = models.FloatField()  # -1.0 .. 1.0
    confidence = models.FloatField()  # 0.0 .. 1.0
    analyzer = models.CharField(max_length=40, default="lexicon")

    class Meta:
        db_table = "news_sentiment"

    def __str__(self) -> str:
        return f"{self.article_id}:{self.label}"


class NewsEntity(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name="entities")
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    entity_text = models.CharField(max_length=150)
    # Resolved link to a domain object (e.g. an Instrument).
    linked_kind = models.CharField(max_length=30, blank=True)
    linked_id = models.UUIDField(null=True, blank=True)
    salience = models.FloatField(default=0.0)

    class Meta:
        db_table = "news_entities"
        indexes = [
            models.Index(fields=["linked_kind", "linked_id"], name="news_entity_link_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.entity_text}"
