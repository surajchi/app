from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.news.models import NewsArticle, NewsCategory, NewsEntity


class NewsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsCategory
        fields = ("id", "slug", "name")
        read_only_fields = fields


class NewsEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsEntity
        fields = ("entity_type", "entity_text", "linked_kind", "linked_id", "salience")
        read_only_fields = fields


def _sentiment_payload(article: NewsArticle) -> dict[str, Any] | None:
    if not hasattr(article, "sentiment"):
        return None
    s = article.sentiment
    return {"label": s.label, "score": s.score, "confidence": s.confidence}


class NewsListSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    sentiment = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = (
            "id",
            "source",
            "title",
            "summary",
            "source_url",
            "image_url",
            "category",
            "impact_score",
            "is_breaking",
            "published_at",
            "sentiment",
        )
        read_only_fields = fields

    def get_sentiment(self, obj: NewsArticle) -> dict[str, Any] | None:
        return _sentiment_payload(obj)


class NewsDetailSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    sentiment = serializers.SerializerMethodField()
    entities = NewsEntitySerializer(many=True, read_only=True)

    class Meta:
        model = NewsArticle
        fields = (
            "id",
            "source",
            "source_url",
            "title",
            "body",
            "summary",
            "author",
            "image_url",
            "language",
            "category",
            "impact_score",
            "is_breaking",
            "published_at",
            "sentiment",
            "entities",
        )
        read_only_fields = fields

    def get_sentiment(self, obj: NewsArticle) -> dict[str, Any] | None:
        return _sentiment_payload(obj)
