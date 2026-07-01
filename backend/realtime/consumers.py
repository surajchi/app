"""WebSocket consumer for live market data + user channels.

Client protocol (JSON):
    {"action": "subscribe",   "channels": ["quotes.AAPL", "alerts"]}
    {"action": "unsubscribe", "channels": ["quotes.AAPL"]}
    {"action": "ping"}

Server frames:
    {"type": "connected"}
    {"type": "subscribed" | "unsubscribed", "channels": [...]}
    {"type": "pong"}
    {"channel": "quotes.AAPL", "type": "quote", "data": {...}}
    {"type": "error", "message": "..."}
"""

from __future__ import annotations

from typing import Any

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from realtime.groups import QUOTE_PREFIX, alerts_group, news_group, notif_group, quote_group


class MarketConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self) -> None:
        self._groups: set[str] = set()
        await self.accept()
        await self.send_json({"type": "connected"})

    async def disconnect(self, code: int) -> None:
        for group in list(self._groups):
            await self.channel_layer.group_discard(group, self.channel_name)
        self._groups.clear()

    async def receive_json(self, content: dict[str, Any], **kwargs: Any) -> None:
        action = content.get("action")
        if action == "ping":
            await self.send_json({"type": "pong"})
        elif action == "subscribe":
            await self._subscribe(content.get("channels", []))
        elif action == "unsubscribe":
            await self._unsubscribe(content.get("channels", []))
        else:
            await self.send_json({"type": "error", "message": "Unknown action."})

    async def _subscribe(self, channels: list[str]) -> None:
        accepted: list[str] = []
        for channel in channels:
            group = self._resolve_group(channel)
            if group is None:
                continue
            await self.channel_layer.group_add(group, self.channel_name)
            self._groups.add(group)
            accepted.append(channel)
        await self.send_json({"type": "subscribed", "channels": accepted})

    async def _unsubscribe(self, channels: list[str]) -> None:
        for channel in channels:
            group = self._resolve_group(channel)
            if group is not None and group in self._groups:
                await self.channel_layer.group_discard(group, self.channel_name)
                self._groups.discard(group)
        await self.send_json({"type": "unsubscribed", "channels": channels})

    def _resolve_group(self, channel: str) -> str | None:
        """Map a client channel name to a layer group, enforcing authorization."""
        if isinstance(channel, str) and channel.startswith(QUOTE_PREFIX):
            symbol = channel[len(QUOTE_PREFIX) :]
            return quote_group(symbol) if symbol else None
        if channel == "news":
            return news_group()
        if isinstance(channel, str) and channel.startswith("news."):
            slug = channel[len("news.") :]
            return news_group(slug) if slug else None
        if channel in ("alerts", "notifications"):
            user = self.scope.get("user")
            if user is not None and getattr(user, "is_authenticated", False):
                return alerts_group(user.id) if channel == "alerts" else notif_group(user.id)
        return None

    # --- channel-layer event handlers --------------------------------------

    async def quote_message(self, event: dict[str, Any]) -> None:
        await self.send_json({"channel": event["group"], "type": "quote", "data": event["data"]})

    async def alert_message(self, event: dict[str, Any]) -> None:
        await self.send_json({"channel": event["group"], "type": "alert", "data": event["data"]})

    async def news_message(self, event: dict[str, Any]) -> None:
        await self.send_json({"channel": event["group"], "type": "news", "data": event["data"]})

    async def notification_message(self, event: dict[str, Any]) -> None:
        await self.send_json(
            {"channel": event["group"], "type": "notification", "data": event["data"]}
        )
