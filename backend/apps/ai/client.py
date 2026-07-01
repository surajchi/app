"""HTTP client for the FastAPI AI service (stdlib urllib; no extra deps)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

_TIMEOUT = 10


class AIServiceError(Exception):
    """Raised when the AI service is unreachable or returns an error."""


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = settings.AI_SERVICE_URL.rstrip("/") + path
    body = json.dumps(payload).encode()
    request = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/json"}
    )
    token = getattr(settings, "AI_SERVICE_TOKEN", "")
    if token:
        request.add_header("X-Service-Token", token)
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:  # noqa: S310
            return json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        raise AIServiceError(str(exc)) from exc


def forecast(series: list[float], horizon: int) -> dict[str, Any]:
    return _post("/forecast", {"series": series, "horizon": horizon})


def technical(series: list[float]) -> dict[str, Any]:
    return _post("/technical", {"series": series})


def sentiment(text: str) -> dict[str, Any]:
    return _post("/sentiment", {"text": text})
