"""Channel interface + send result."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from apps.notifications.models import Notification, NotificationDelivery


@dataclasses.dataclass
class SendResult:
    ok: bool
    provider_id: str = ""
    error: str = ""


@runtime_checkable
class NotificationChannel(Protocol):
    name: str

    def send(self, notification: Notification, delivery: NotificationDelivery) -> SendResult: ...
