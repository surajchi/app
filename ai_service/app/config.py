"""Runtime config for the AI service (env-driven)."""
from __future__ import annotations

import os


class Settings:
    # Shared secret for service-to-service auth. Empty = auth disabled (dev/tests).
    token: str = os.getenv("AI_SERVICE_TOKEN", "")
    version: str = "1.0.0"


settings = Settings()
