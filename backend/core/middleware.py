"""Cross-cutting HTTP middleware."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class RequestIDMiddleware:
    """Attach a correlation id to every request and echo it on the response.

    Honors an inbound `X-Request-ID` (set by the edge proxy) or generates one.
    The id is stored on ``request.request_id`` for downstream use/logging.
    """

    HEADER = "X-Request-ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get(self.HEADER) or uuid.uuid4().hex
        request.request_id = request_id  # type: ignore[attr-defined]
        response = self.get_response(request)
        response[self.HEADER] = request_id
        return response
