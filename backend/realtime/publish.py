"""Publish helpers used by tasks/services to push frames to WebSocket groups."""

from __future__ import annotations

from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from realtime.groups import alerts_group, news_group, notif_group, quote_group


def publish_quote(symbol: str, data: dict[str, Any]) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    group = quote_group(symbol)
    async_to_sync(layer.group_send)(group, {"type": "quote.message", "group": group, "data": data})


def publish_alert(user_id: str, data: dict[str, Any]) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    group = alerts_group(user_id)
    async_to_sync(layer.group_send)(group, {"type": "alert.message", "group": group, "data": data})


def publish_notification(user_id: str, data: dict[str, Any]) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    group = notif_group(user_id)
    async_to_sync(layer.group_send)(
        group, {"type": "notification.message", "group": group, "data": data}
    )


def publish_news(data: dict[str, Any], category: str | None = None) -> None:
    """Broadcast to the global 'news' group and, if given, a per-category group."""
    layer = get_channel_layer()
    if layer is None:
        return
    groups = [news_group()]
    if category:
        groups.append(news_group(category))
    for group in groups:
        async_to_sync(layer.group_send)(
            group, {"type": "news.message", "group": group, "data": data}
        )
