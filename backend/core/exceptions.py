"""Custom DRF exception handler producing the standard error envelope."""

from __future__ import annotations

import logging
from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("finpulse")


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    response = drf_exception_handler(exc, context)
    request = context.get("request")
    request_id = getattr(request, "request_id", None)

    if response is None:
        # Unhandled -> 500. Log with the correlation id; never leak internals.
        logger.exception("Unhandled exception", extra={"request_id": request_id})
        return Response(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal server error occurred.",
                    "details": None,
                },
            },
            status=500,
        )

    code = str(getattr(exc, "default_code", "error")).upper()
    message = "Request failed."
    details: Any = None

    data = response.data
    if isinstance(data, dict):
        if "detail" in data and len(data) == 1:
            message = str(data["detail"])
        else:
            message = "Validation failed."
            details = data
    elif isinstance(data, list):
        message = "Validation failed."
        details = {"non_field_errors": data}

    response.data = {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
    }
    return response
