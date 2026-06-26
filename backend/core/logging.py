"""Structured JSON log formatter (used in non-DEBUG environments)."""

from __future__ import annotations

import datetime as dt
import json
import logging


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON for log aggregation (OpenSearch)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "time": dt.datetime.fromtimestamp(record.created, tz=dt.UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)
