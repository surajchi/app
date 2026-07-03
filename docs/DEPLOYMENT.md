# FinPulse — Deployment Runbook

A practical, step-by-step guide to running FinPulse in production. For the
design rationale see [architecture/10-devops-deployment.md](architecture/10-devops-deployment.md).

Everything ships free of paid third-party APIs by default: market data, news,
sentiment, AI, and payments all default to self-contained providers. Swap in
real providers via environment variables when you're ready — no code changes.

---

## 1. Topology

| Service   | Image / command                                              | Purpose                                  |
|-----------|--------------------------------------------------------------|------------------------------------------|
| `api`     | `gunicorn config.asgi -k uvicorn.workers.UvicornWorker`      | HTTP + WebSocket (ASGI) app              |
| `worker`  | `celery -A config worker`                                    | Async tasks (dispatch, ingest, alerts)   |
| `beat`    | `celery -A config beat`                                      | Scheduled jobs (quotes, news, renewals)  |
| `ai`      | `uvicorn app.main:app` (FastAPI)                             | Forecasting / technical / sentiment      |
| `postgres`| TimescaleDB                                                  | Primary datastore (+ hypertables)        |
| `redis`   | Redis                                                        | Cache, Celery broker/result, Channels    |
| `opensearch` | OpenSearch                                                | News full-text search (DB fallback)      |
| `minio`   | MinIO                                                        | S3-compatible object storage             |
| `nginx`   | Nginx                                                        | TLS termination + reverse proxy          |

The base `docker-compose.yml` is the **production** definition (build images,
`restart: unless-stopped`, healthchecks, `collectstatic` + `migrate` on boot).
`docker-compose.override.yml` layers **development** conveniences (source mounts,
autoreload) and is applied automatically by `docker compose` locally — so do
**not** use it in production.

---

## 2. Prerequisites

- Docker Engine + Compose v2 (or Kubernetes; the images are plain OCI).
- A managed Postgres with the **TimescaleDB** extension, or the bundled container.
- A domain + TLS certificate terminated at Nginx (or an upstream load balancer).

---

## 3. Configure environment

```bash
cp backend/.env.example backend/.env
cp apps/mobile/.env.example apps/mobile/.env   # for building the web/app client
```

Then edit `backend/.env` for production. **Minimum changes from the sample:**

```dotenv
ENV=production
DJANGO_SETTINGS_MODULE=config.settings.prod
DEBUG=false
SECRET_KEY=<64+ random chars>                 # python -c "import secrets;print(secrets.token_urlsafe(64))"
ALLOWED_HOSTS=api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://app.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://app.yourdomain.com

# RS256 is required in prod (dev falls back to HS256). Generate a keypair:
#   openssl genrsa -out jwtRS256.key 2048
#   openssl rsa -in jwtRS256.key -pubout -out jwtRS256.key.pub
JWT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----

# Managed datastores (or leave the compose defaults for the bundled containers):
DATABASE_URL=postgres://user:pass@db-host:5432/finpulse
REDIS_URL=redis://redis-host:6379/0
CELERY_BROKER_URL=redis://redis-host:6379/1
CELERY_RESULT_BACKEND=redis://redis-host:6379/2
CHANNELS_REDIS_URL=redis://redis-host:6379/3
```

Optional production integrations (all safe to leave blank/default):

- **Email**: set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` + `EMAIL_HOST*`.
- **Real market/news**: `MARKET_DATA_PROVIDER`, `NEWS_PROVIDER=rss` + `NEWS_RSS_FEEDS`.
- **Payments**: `PAYMENT_PROVIDER` (defaults to the free `mock`) + `PAYMENT_WEBHOOK_SECRET`.
- **Error monitoring**: `SENTRY_DSN` (disabled entirely when blank).

`config.settings.prod` enforces HTTPS redirect, HSTS, secure cookies,
`X-Frame-Options: DENY`, content-type nosniff, referrer policy, and disables the
browsable API.

---

## 4. Deploy

```bash
# Build images
docker compose -f docker-compose.yml build

# Start datastores first, then the app tier
docker compose -f docker-compose.yml up -d postgres redis opensearch minio
docker compose -f docker-compose.yml up -d api worker beat ai nginx
```

`api` runs `collectstatic` (WhiteNoise, compressed+hashed) and `migrate` on
startup, so a normal boot applies pending migrations. To run migrations
explicitly (e.g. a managed DB with a migration gate):

```bash
docker compose -f docker-compose.yml run --rm api python manage.py migrate
```

Create the first superuser:

```bash
docker compose -f docker-compose.yml run --rm api python manage.py createsuperuser
```

Seed reference data (idempotent): RBAC roles and billing plans are seeded by
data migrations automatically. Market instruments can be seeded with:

```bash
docker compose -f docker-compose.yml run --rm api python manage.py seed_markets
```

---

## 5. Verify

```bash
# Deployment security audit (should report no issues under prod settings)
docker compose run --rm api python manage.py check --deploy

# Liveness / readiness (readiness checks DB + cache)
curl -sf https://api.yourdomain.com/healthz/
curl -sf https://api.yourdomain.com/readyz/

# API docs
open https://api.yourdomain.com/api/docs/       # Swagger UI
```

---

## 6. Scaling

- **api**: increase `--workers` (rule of thumb `2 × vCPU + 1`) or run more `api`
  replicas behind Nginx. WebSockets are Redis-backed (Channels), so replicas
  share subscriptions.
- **worker**: raise `--concurrency` or add replicas. Tasks are idempotent and
  safe to run across multiple workers.
- **beat**: run **exactly one** replica (it is the singleton scheduler).
- **postgres/redis**: use managed, replicated instances in production.

Scheduled jobs (Celery beat): market quote polling, news ingestion, price-alert
evaluation, and subscription renewals — intervals are env-tunable
(`MARKET_POLL_INTERVAL`, `NEWS_POLL_INTERVAL`, `ALERT_EVAL_INTERVAL`,
`BILLING_RENEWAL_INTERVAL`).

---

## 7. Operations

- **Logs**: JSON to stdout (parse with your log stack). `LOG_LEVEL` tunes verbosity.
  Every request carries an `X-Request-ID` for correlation.
- **Rate limiting**: DRF scoped throttles — `THROTTLE_AUTH`, `THROTTLE_ANON`,
  `THROTTLE_USER`.
- **Backups**: snapshot Postgres (incl. Timescale hypertables) and MinIO buckets.
- **Zero-downtime migrations**: prefer additive migrations; deploy code that
  tolerates both schemas, migrate, then remove old paths.
- **Rollback**: redeploy the previous image tag; keep migrations backward-safe.

---

## 8. CI

GitHub Actions runs the backend gate (ruff, black, mypy, pytest) and the
frontend checks (typecheck, lint, jest). Coverage locally:

```bash
docker compose run --rm api pytest --cov --cov-report=term-missing
```
