"""Test settings — fast, deterministic, Postgres-backed (parity with prod)."""

from .base import *  # noqa: F401,F403

DEBUG = False
# Tests run with HS256 signed by SECRET_KEY (no RS256 keys needed in CI).

# Speed up password hashing in tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Use the local-memory cache so tests don't require a running Redis for caching.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Capture emails in mail.outbox instead of printing them.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# In-memory channel layer for WebSocket tests (no Redis needed).
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# Don't hit OpenSearch during tests (search is tested via mocks + DB fallback).
SEARCH_ENABLED = False

# Deterministic, offline market data in tests (no network to Stooq).
MARKET_DATA_PROVIDER = "synthetic"

# Run Celery tasks eagerly (synchronously) in tests.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable throttling during tests.
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = ()  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405
