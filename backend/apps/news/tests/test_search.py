from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.news.pipeline import process
from integrations.news.base import RawArticle

pytestmark = pytest.mark.django_db


def _raw(title: str, url: str) -> RawArticle:
    return RawArticle(
        source="synthetic", url=url, title=title, body="", published_at=timezone.now()
    )


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_to_document_builds_expected_fields():
    from search.news_index import to_document

    article = process(_raw("Apple shares surge on earnings beat", "https://n/doc"))
    doc = to_document(article)
    assert doc["title"].startswith("Apple")
    assert "category" in doc
    assert "sentiment" in doc
    assert isinstance(doc["symbols"], list)


def test_search_db_path_when_search_disabled(client):
    # SEARCH_ENABLED is False in test settings -> DB search path.
    process(_raw("Reliance posts record quarterly profit", "https://n/s1"))
    resp = client.get("/api/v1/news/search/?q=Reliance")
    assert resp.status_code == 200
    assert any("Reliance" in row["title"] for row in resp.json()["data"])


@override_settings(SEARCH_ENABLED=True)
def test_search_opensearch_path_mocked(client):
    article = process(_raw("Bitcoin rallies hard today", "https://n/s2"))
    with patch("search.news_index.search_news", return_value=[str(article.id)]):
        resp = client.get("/api/v1/news/search/?q=bitcoin")
    assert resp.status_code == 200
    assert str(article.id) in [row["id"] for row in resp.json()["data"]]


@override_settings(SEARCH_ENABLED=True)
def test_search_falls_back_to_db_on_error(client):
    process(_raw("Gold gains on inflation fears", "https://n/s3"))
    with patch("search.news_index.search_news", side_effect=RuntimeError("opensearch down")):
        resp = client.get("/api/v1/news/search/?q=Gold")
    assert resp.status_code == 200
    assert any("Gold" in row["title"] for row in resp.json()["data"])
