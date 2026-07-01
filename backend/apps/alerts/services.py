"""Alert evaluation: match active rules against quotes and news, then fire.

Firing creates an ``Alert`` history row plus a notification (routed through the
Phase 6A notification engine, so channel/quiet-hour rules apply). ``once`` rules
deactivate after firing; ``recurring`` rules honour ``cooldown_seconds``.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.alerts.constants import NEWS_TRIGGERS, PRICE_TRIGGERS, Frequency, TriggerType
from apps.alerts.models import Alert, AlertRule

if TYPE_CHECKING:
    from datetime import datetime

    from apps.news.models import NewsArticle

logger = logging.getLogger("finpulse")


def _active_rules(trigger_types: tuple[str, ...]) -> QuerySet[AlertRule]:
    now = timezone.now()
    return (
        AlertRule.objects.filter(is_active=True, trigger_type__in=list(trigger_types))
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        .select_related("user", "instrument")
    )


def _on_cooldown(rule: AlertRule, now: datetime) -> bool:
    if not rule.last_triggered_at or rule.cooldown_seconds <= 0:
        return False
    return now - rule.last_triggered_at < timedelta(seconds=rule.cooldown_seconds)


def _fire(rule: AlertRule, title: str, body: str, snapshot: dict[str, Any]) -> Alert:
    from apps.notifications.services import create_notification

    notification = create_notification(
        user=rule.user,
        type="alert",
        title=title,
        body=body,
        priority=rule.priority,
        data={"rule_id": str(rule.id), "snapshot": snapshot},
        channels=list(rule.channels) or None,
    )
    alert = Alert.objects.create(
        rule=rule, user=rule.user, snapshot=snapshot, notification=notification
    )
    rule.last_triggered_at = timezone.now()
    if rule.frequency == Frequency.ONCE:
        rule.is_active = False
    rule.save(update_fields=["last_triggered_at", "is_active", "updated_at"])
    logger.info("alerts.fired", extra={"rule_id": str(rule.id), "trigger": rule.trigger_type})
    return alert


# --- Price rules ------------------------------------------------------------


def _price_hit(rule: AlertRule, quote: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    price = quote.get("price")
    change_pct = quote.get("change_percent")
    value = (rule.condition or {}).get("value")
    snapshot = {"price": price, "change_percent": change_pct, "threshold": value}
    if value is None:
        return False, snapshot
    if rule.trigger_type == TriggerType.PRICE_ABOVE:
        return (price is not None and price >= value), snapshot
    if rule.trigger_type == TriggerType.PRICE_BELOW:
        return (price is not None and price <= value), snapshot
    if rule.trigger_type == TriggerType.PCT_CHANGE:
        return (change_pct is not None and abs(change_pct) >= value), snapshot
    return False, snapshot


def _price_body(rule: AlertRule, snapshot: dict[str, Any]) -> str:
    symbol = rule.instrument.symbol if rule.instrument_id else "instrument"
    if rule.trigger_type == TriggerType.PCT_CHANGE:
        return f"{symbol} moved {snapshot['change_percent']}% (threshold {snapshot['threshold']}%)."
    return f"{symbol} is {snapshot['price']} (threshold {snapshot['threshold']})."


def evaluate_price_rules() -> int:
    """Evaluate all active price rules against the latest cached quotes."""
    from apps.markets import cache as market_cache

    now = timezone.now()
    fired = 0
    rules = _active_rules(PRICE_TRIGGERS).exclude(instrument__isnull=True)
    for rule in rules:
        if _on_cooldown(rule, now):
            continue
        quote = market_cache.get_quote(rule.instrument_id)
        if not quote:
            continue
        hit, snapshot = _price_hit(rule, quote)
        if hit:
            _fire(rule, rule.name, _price_body(rule, snapshot), snapshot)
            fired += 1
    return fired


# --- News rules -------------------------------------------------------------


def check_news_article(article: NewsArticle) -> int:
    """Evaluate keyword/sentiment rules against one freshly ingested article."""
    from apps.news.models import NewsSentiment

    now = timezone.now()
    text = f"{article.title} {article.body}".lower()
    label = NewsSentiment.objects.filter(article=article).values_list("label", flat=True).first()
    linked_ids = set(
        article.entities.filter(linked_kind="instrument")
        .exclude(linked_id__isnull=True)
        .values_list("linked_id", flat=True)
    )

    fired = 0
    for rule in _active_rules(NEWS_TRIGGERS):
        if _on_cooldown(rule, now):
            continue
        if rule.instrument_id and rule.instrument_id not in linked_ids:
            continue
        cond = rule.condition or {}
        hit = False
        if rule.trigger_type == TriggerType.NEWS_KEYWORD:
            keyword = str(cond.get("keyword", "")).lower().strip()
            hit = bool(keyword) and keyword in text
        elif rule.trigger_type == TriggerType.SENTIMENT:
            hit = label is not None and label == cond.get("label")
        if hit:
            snapshot = {"article_id": str(article.id), "title": article.title, "label": label}
            _fire(rule, rule.name, article.title[:200], snapshot)
            fired += 1
    return fired
