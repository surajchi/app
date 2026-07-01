import pytest
from rest_framework.test import APIClient

from apps.alerts.models import Alert, AlertRule
from apps.alerts.services import check_news_article, evaluate_price_rules
from apps.markets import cache as market_cache
from apps.markets.tests.factories import InstrumentFactory
from apps.news.models import NewsArticle, NewsEntity, NewsSentiment
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _rule(user, instrument, **kwargs) -> AlertRule:
    defaults = {
        "name": "Rule",
        "instrument": instrument,
        "trigger_type": "price_above",
        "condition": {"value": 100},
        "frequency": "once",
        "priority": "high",
    }
    defaults.update(kwargs)
    return AlertRule.objects.create(user=user, **defaults)


def _article(title="Market update", body="", published_at=None) -> NewsArticle:
    from django.utils import timezone

    return NewsArticle.objects.create(
        source="test",
        source_url=f"https://example.com/{title}".replace(" ", "-"),
        url_hash=title.replace(" ", "-"),
        simhash=0,
        title=title,
        body=body,
        published_at=published_at or timezone.now(),
    )


# --- price evaluation -------------------------------------------------------


def test_price_above_fires_and_notifies():
    user = UserFactory()
    inst = InstrumentFactory()
    rule = _rule(user, inst, trigger_type="price_above", condition={"value": 100})
    market_cache.set_quote(inst.id, {"price": 150.0, "change_percent": 2.0})

    assert evaluate_price_rules() == 1
    alert = Alert.objects.get(rule=rule)
    assert alert.notification is not None
    assert alert.notification.type == "alert"
    rule.refresh_from_db()
    assert rule.is_active is False  # "once" deactivates


def test_price_above_does_not_fire_below_threshold():
    user = UserFactory()
    inst = InstrumentFactory()
    _rule(user, inst, trigger_type="price_above", condition={"value": 100})
    market_cache.set_quote(inst.id, {"price": 50.0, "change_percent": 0.0})
    assert evaluate_price_rules() == 0
    assert Alert.objects.count() == 0


def test_price_below_fires():
    user = UserFactory()
    inst = InstrumentFactory()
    _rule(user, inst, trigger_type="price_below", condition={"value": 100})
    market_cache.set_quote(inst.id, {"price": 80.0, "change_percent": -1.0})
    assert evaluate_price_rules() == 1


def test_pct_change_uses_absolute_move():
    user = UserFactory()
    inst = InstrumentFactory()
    _rule(user, inst, trigger_type="pct_change", condition={"value": 3})
    market_cache.set_quote(inst.id, {"price": 10.0, "change_percent": -5.0})
    assert evaluate_price_rules() == 1


def test_recurring_respects_cooldown():
    user = UserFactory()
    inst = InstrumentFactory()
    _rule(
        user,
        inst,
        trigger_type="price_above",
        condition={"value": 100},
        frequency="recurring",
        cooldown_seconds=3600,
    )
    market_cache.set_quote(inst.id, {"price": 150.0, "change_percent": 2.0})
    assert evaluate_price_rules() == 1
    # Second sweep is within cooldown -> suppressed, rule still active.
    assert evaluate_price_rules() == 0
    assert Alert.objects.count() == 1


def test_missing_quote_is_skipped():
    user = UserFactory()
    inst = InstrumentFactory()
    _rule(user, inst, trigger_type="price_above", condition={"value": 100})
    assert evaluate_price_rules() == 0


# --- news evaluation --------------------------------------------------------


def test_news_keyword_fires():
    user = UserFactory()
    AlertRule.objects.create(
        user=user,
        name="Fed watch",
        trigger_type="news_keyword",
        condition={"keyword": "fed"},
    )
    article = _article(title="The Fed raises rates", body="details")
    assert check_news_article(article) == 1
    assert Alert.objects.filter(user=user).count() == 1


def test_news_keyword_no_match():
    user = UserFactory()
    AlertRule.objects.create(
        user=user,
        name="Fed watch",
        trigger_type="news_keyword",
        condition={"keyword": "fed"},
    )
    article = _article(title="Crypto rallies", body="details")
    assert check_news_article(article) == 0


def test_news_sentiment_fires():
    user = UserFactory()
    AlertRule.objects.create(
        user=user,
        name="Bad news",
        trigger_type="sentiment",
        condition={"label": "negative"},
    )
    article = _article(title="Markets crash")
    NewsSentiment.objects.create(article=article, label="negative", score=-0.8, confidence=0.9)
    assert check_news_article(article) == 1


def test_news_instrument_scope_filters():
    user = UserFactory()
    inst = InstrumentFactory()
    AlertRule.objects.create(
        user=user,
        name="AAPL news",
        instrument=inst,
        trigger_type="news_keyword",
        condition={"keyword": "earnings"},
    )
    # Article mentions the keyword but is not linked to the instrument.
    unlinked = _article(title="Company earnings beat", body="x")
    assert check_news_article(unlinked) == 0

    linked = _article(title="More earnings ahead", body="y")
    NewsEntity.objects.create(
        article=linked,
        entity_type="org",
        entity_text="AAPL",
        linked_kind="instrument",
        linked_id=inst.id,
    )
    assert check_news_article(linked) == 1


# --- API --------------------------------------------------------------------


def test_rules_require_auth(client):
    assert client.get("/api/v1/alerts/rules/").status_code == 401


def test_create_and_list_rule(client):
    user = UserFactory()
    inst = InstrumentFactory()
    client.force_authenticate(user)
    resp = client.post(
        "/api/v1/alerts/rules/",
        {
            "name": "My alert",
            "instrument": str(inst.id),
            "trigger_type": "price_above",
            "condition": {"value": 100},
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert AlertRule.objects.filter(user=user, name="My alert").exists()
    assert len(client.get("/api/v1/alerts/rules/").json()["data"]) == 1


def test_rules_are_user_scoped(client):
    owner = UserFactory()
    other = UserFactory()
    _rule(owner, InstrumentFactory())
    client.force_authenticate(other)
    assert client.get("/api/v1/alerts/rules/").json()["data"] == []


def test_price_rule_requires_instrument(client):
    user = UserFactory()
    client.force_authenticate(user)
    resp = client.post(
        "/api/v1/alerts/rules/",
        {"name": "bad", "trigger_type": "price_above", "condition": {"value": 1}},
        format="json",
    )
    assert resp.status_code == 400


def test_news_keyword_rule_requires_keyword(client):
    user = UserFactory()
    client.force_authenticate(user)
    resp = client.post(
        "/api/v1/alerts/rules/",
        {"name": "bad", "trigger_type": "news_keyword", "condition": {}},
        format="json",
    )
    assert resp.status_code == 400


def test_history_lists_fires(client):
    user = UserFactory()
    inst = InstrumentFactory()
    _rule(user, inst, trigger_type="price_above", condition={"value": 100})
    market_cache.set_quote(inst.id, {"price": 150.0, "change_percent": 2.0})
    evaluate_price_rules()
    client.force_authenticate(user)
    data = client.get("/api/v1/alerts/history/").json()["data"]
    assert len(data) == 1
    assert data[0]["trigger_type"] == "price_above"
