import datetime as dt

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.markets.tests.factories import InstrumentFactory
from apps.news.models import NewsArticle, NewsEntity
from apps.news.pipeline import process
from apps.news.tasks import ingest_news
from apps.news.tests.factories import NewsArticleFactory
from integrations.news.base import RawArticle

pytestmark = pytest.mark.django_db


def _raw(title: str, body: str = "", url: str = "https://news.example/x/1") -> RawArticle:
    return RawArticle(
        source="synthetic", url=url, title=title, body=body, published_at=timezone.now()
    )


@pytest.fixture
def client() -> APIClient:
    return APIClient()


# --- pipeline ---------------------------------------------------------------


def test_pipeline_creates_article_with_sentiment_and_category():
    article = process(
        _raw("Apple shares surge as quarterly earnings beat estimates", "Strong profit and growth.")
    )
    assert article is not None
    assert article.sentiment.label == "positive"
    assert article.category is not None
    assert article.summary


def test_pipeline_negative_sentiment():
    article = process(_raw("Markets plunge as losses mount and fear spreads", url="https://n/neg"))
    assert article is not None
    assert article.sentiment.label == "negative"


def test_pipeline_links_instrument_entity():
    InstrumentFactory(symbol="AAPL", name="Apple Inc.")
    article = process(_raw("Apple shares jump after earnings beat", url="https://n/aapl"))
    assert article is not None
    assert NewsEntity.objects.filter(article=article, linked_kind="instrument").exists()


def test_pipeline_dedup_exact_url():
    raw = _raw("Some unique market headline today", url="https://n/dup")
    assert process(raw) is not None
    assert process(raw) is None  # same URL -> duplicate


def test_pipeline_near_duplicate_simhash():
    process(_raw("Gold gains as inflation fears lift demand sharply", url="https://n/g1"))
    # Same text, different URL -> caught by simhash near-dup.
    dup = process(_raw("Gold gains as inflation fears lift demand sharply", url="https://n/g2"))
    assert dup is None


# --- ingest task ------------------------------------------------------------


def test_ingest_news_task_and_dedup():
    created = ingest_news()
    assert created > 0
    assert NewsArticle.objects.count() == created
    # Re-running within the same hour yields duplicates -> nothing new.
    assert ingest_news() == 0


# --- API --------------------------------------------------------------------


def test_feed_list(client):
    NewsArticleFactory.create_batch(3)
    resp = client.get("/api/v1/news/")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 3


def test_detail(client):
    article = process(_raw("Bitcoin rallies past resistance", url="https://n/btc"))
    resp = client.get(f"/api/v1/news/{article.id}/")
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["title"] == "Bitcoin rallies past resistance"
    assert "sentiment" in body and "entities" in body


def test_filter_by_symbol(client):
    InstrumentFactory(symbol="AAPL", name="Apple Inc.")
    process(_raw("Apple shares surge on strong results", url="https://n/aapl2"))
    NewsArticleFactory(title="Unrelated headline", url_hash="f" * 64, source_url="https://n/unrel")
    resp = client.get("/api/v1/news/?symbol=AAPL")
    assert resp.status_code == 200
    titles = [row["title"] for row in resp.json()["data"]]
    assert any("Apple" in t for t in titles)
    assert "Unrelated headline" not in titles


def test_trending_orders_by_impact(client):
    NewsArticleFactory(title="low", url_hash="a" * 64, source_url="https://n/low", impact_score=10)
    NewsArticleFactory(
        title="high", url_hash="b" * 64, source_url="https://n/high", impact_score=90
    )
    resp = client.get("/api/v1/news/trending/")
    assert resp.status_code == 200
    assert resp.json()["data"][0]["title"] == "high"


def test_categories(client):
    process(_raw("Nifty 50 hits record high", url="https://n/nifty"))
    resp = client.get("/api/v1/news/categories/")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


def test_search_q(client):
    process(_raw("Reliance posts record quarterly profit", url="https://n/ril"))
    resp = client.get("/api/v1/news/?q=Reliance")
    assert resp.status_code == 200
    assert any("Reliance" in row["title"] for row in resp.json()["data"])


def test_published_at_recent():
    article = process(_raw("Fresh markets update headline", url="https://n/fresh"))
    assert article is not None
    assert timezone.now() - article.published_at < dt.timedelta(minutes=5)
