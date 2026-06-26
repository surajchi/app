# syntax=docker/dockerfile:1
# Multi-stage: shared `base`, a `dev` target (with test/lint tooling), and a
# slim non-root `prod` target. Compose builds `prod` by default; the api service
# overrides to `dev` in docker-compose.override.yml.

FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.local
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements ./requirements
RUN pip install -r requirements/base.txt
COPY . .

# --- Development image: adds pytest / ruff / black / mypy --------------------
FROM base AS dev
RUN pip install -r requirements/dev.txt
EXPOSE 8000
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Production image: slim, non-root ---------------------------------------
FROM base AS prod
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["gunicorn", "config.asgi:application", "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
