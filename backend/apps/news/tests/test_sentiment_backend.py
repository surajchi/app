from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.news.pipeline import process
from integrations.news.base import RawArticle

pytestmark = pytest.mark.django_db


def _raw(title: str, url: str) -> RawArticle:
    return RawArticle(
        source="synthetic", url=url, title=title, body="", published_at=timezone.now()
    )


@override_settings(NEWS_SENTIMENT_BACKEND="ai_service")
def test_pipeline_uses_ai_sentiment():
    ai_result = {"label": "positive", "score": 0.9, "confidence": 0.8, "model": "lexicon-v1"}
    with patch("apps.ai.client.sentiment", return_value=ai_result):
        article = process(_raw("A perfectly neutral headline about things", "https://n/ai1"))
    assert article is not None
    assert article.sentiment.label == "positive"
    assert article.sentiment.analyzer == "lexicon-v1"


@override_settings(NEWS_SENTIMENT_BACKEND="ai_service")
def test_pipeline_falls_back_to_lexicon_on_ai_error():
    with patch("apps.ai.client.sentiment", side_effect=RuntimeError("ai down")):
        article = process(_raw("Markets plunge on heavy losses and fear", "https://n/ai2"))
    assert article is not None
    assert article.sentiment.analyzer == "lexicon"
    assert article.sentiment.label == "negative"
