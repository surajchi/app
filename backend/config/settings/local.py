"""Local development settings."""

from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK

# Browsable API is convenient during local development.
REST_FRAMEWORK = {**REST_FRAMEWORK}

# Permissive CORS for Expo dev tooling (origins still come from env).
CORS_ALLOW_ALL_ORIGINS = False
