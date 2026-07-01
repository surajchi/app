"""
Base Django settings shared across all environments.

Environment-specific modules (local / prod / test) import everything from here
and override as needed. All configuration is sourced from environment variables
(12-factor) via django-environ — never hardcode secrets.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# backend/ directory (config/settings/base.py -> config -> backend)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Read a local .env if present (repo root or backend/); in Docker env is injected.
for candidate in (BASE_DIR.parent / ".env", BASE_DIR / ".env"):
    if candidate.exists():
        environ.Env.read_env(str(candidate))
        break

# --- Core -------------------------------------------------------------------
SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
ENV = env.str("ENV", default="local")

# --- Applications -----------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "channels",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.users",
    "apps.rbac",
    "apps.profiles",
    "apps.accounts",
    "apps.authentication",
    "apps.markets",
    "apps.news",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --- Middleware -------------------------------------------------------------
MIDDLEWARE = [
    "core.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database ---------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)

# --- Auth -------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N / TZ --------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static -----------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Cache (Redis) ----------------------------------------------------------
REDIS_URL = env.str("REDIS_URL", default="redis://redis:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# --- Channels (WebSockets) --------------------------------------------------
CHANNELS_REDIS_URL = env.str("CHANNELS_REDIS_URL", default="redis://redis:6379/3")
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [CHANNELS_REDIS_URL]},
    }
}

# --- Celery -----------------------------------------------------------------
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default="redis://redis:6379/1")
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", default="redis://redis:6379/2")
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULE = {
    "poll-market-quotes": {
        "task": "apps.markets.tasks.poll_quotes",
        "schedule": env.float("MARKET_POLL_INTERVAL", default=15.0),
    },
    "ingest-news": {
        "task": "apps.news.tasks.ingest_news",
        "schedule": env.float("NEWS_POLL_INTERVAL", default=60.0),
    },
}

# --- Market data ------------------------------------------------------------
MARKET_DATA_PROVIDER = env.str("MARKET_DATA_PROVIDER", default="synthetic")

# --- News -------------------------------------------------------------------
NEWS_PROVIDER = env.str("NEWS_PROVIDER", default="synthetic")
NEWS_RSS_FEEDS = env.list("NEWS_RSS_FEEDS", default=[])

# --- Search (OpenSearch) ----------------------------------------------------
OPENSEARCH_URL = env.str("OPENSEARCH_URL", default="http://opensearch:9200")
SEARCH_ENABLED = env.bool("SEARCH_ENABLED", default=True)

# --- DRF --------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": (
        "core.renderers.EnvelopeJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.ScopedRateThrottle",),
    "DEFAULT_THROTTLE_RATES": {
        "auth": env.str("THROTTLE_AUTH", default="20/min"),
        "anon": env.str("THROTTLE_ANON", default="60/min"),
        "user": env.str("THROTTLE_USER", default="1000/min"),
    },
}

# --- JWT --------------------------------------------------------------------
# RS256 when an asymmetric keypair is supplied (required in prod); otherwise
# HS256 with SECRET_KEY for zero-setup, multi-worker-safe local development.
JWT_PRIVATE_KEY = env.str("JWT_PRIVATE_KEY", default="").replace("\\n", "\n")
JWT_PUBLIC_KEY = env.str("JWT_PUBLIC_KEY", default="").replace("\\n", "\n")

if JWT_PRIVATE_KEY and JWT_PUBLIC_KEY:
    _JWT_ALGORITHM = "RS256"
    _JWT_SIGNING_KEY = JWT_PRIVATE_KEY
    _JWT_VERIFYING_KEY = JWT_PUBLIC_KEY
else:
    if not DEBUG:
        raise ImproperlyConfigured(
            "JWT_PRIVATE_KEY and JWT_PUBLIC_KEY (RS256) are required when DEBUG=False."
        )
    _JWT_ALGORITHM = "HS256"
    _JWT_SIGNING_KEY = SECRET_KEY
    _JWT_VERIFYING_KEY = ""

SIMPLE_JWT = {
    "ALGORITHM": _JWT_ALGORITHM,
    "SIGNING_KEY": _JWT_SIGNING_KEY,
    "VERIFYING_KEY": _JWT_VERIFYING_KEY,
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("ACCESS_TOKEN_LIFETIME_MIN", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("REFRESH_TOKEN_LIFETIME_DAYS", default=30)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- Email ------------------------------------------------------------------
# Dev defaults to the console backend (emails print to logs; no SMTP needed).
EMAIL_BACKEND = env.str("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env.str("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="FinPulse <no-reply@finpulse.app>")

# Base URL used to build links in emails (deep links into the app).
FRONTEND_URL = env.str("FRONTEND_URL", default="http://localhost:8081")

# --- Auth flows (verification / OTP / 2FA / OAuth) --------------------------
EMAIL_VERIFICATION_TTL = env.int("EMAIL_VERIFICATION_TTL", default=86400)  # 24h
OTP_TTL_SECONDS = env.int("OTP_TTL_SECONDS", default=300)  # 5 min
OTP_LENGTH = env.int("OTP_LENGTH", default=6)
OTP_MAX_ATTEMPTS = env.int("OTP_MAX_ATTEMPTS", default=5)
TWO_FACTOR_ISSUER = env.str("TWO_FACTOR_ISSUER", default="FinPulse")
TWO_FA_CHALLENGE_TTL = env.int("TWO_FA_CHALLENGE_TTL", default=300)  # 5 min

# OAuth client IDs (required only to use the respective provider live).
GOOGLE_CLIENT_ID = env.str("GOOGLE_CLIENT_ID", default="")
APPLE_CLIENT_ID = env.str("APPLE_CLIENT_ID", default="")

# --- OpenAPI / Spectacular --------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "FinPulse API",
    "DESCRIPTION": "AI-Powered Forex & Global Market Intelligence Platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# --- CORS / CSRF ------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:8081"])
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:8081"])

# --- Logging ----------------------------------------------------------------
LOG_LEVEL = env.str("LOG_LEVEL", default="INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "core.logging.JsonFormatter"},
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if not DEBUG else "plain",
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "finpulse": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}
