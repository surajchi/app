"""Standard API response envelope renderer.

All JSON responses are wrapped so clients get a predictable shape:

    success:  {"success": true, "data": <payload>, "meta": {...}?}
    error:    {"success": false, "error": {"code", "message", "details"}}

Errors are pre-shaped by ``core.exceptions.custom_exception_handler`` and pass
through untouched. Paginated payloads ({count, next, previous, results}) are
split into ``data`` + ``meta``.
"""

from __future__ import annotations

from typing import Any

from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, Any] | None = None,
    ) -> bytes:
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        status_code = getattr(response, "status_code", 200)
        payload = self._wrap(data, status_code)
        if payload is None:
            return b""
        return super().render(payload, accepted_media_type, renderer_context)

    @staticmethod
    def _wrap(data: Any, status_code: int) -> dict[str, Any] | None:
        if data is None:
            return None

        # Already enveloped (by the exception handler or a view).
        if isinstance(data, dict):
            if data.get("success") is False and "error" in data:
                return data
            if data.get("success") is True and "data" in data:
                return data

        if status_code >= 400:
            return {
                "success": False,
                "error": {"code": "ERROR", "message": "Request failed.", "details": data},
            }

        # Paginated responses -> data + meta.
        if isinstance(data, dict) and "results" in data and "count" in data:
            return {
                "success": True,
                "data": data.get("results"),
                "meta": {
                    "count": data.get("count"),
                    "next": data.get("next"),
                    "previous": data.get("previous"),
                },
            }

        return {"success": True, "data": data}
