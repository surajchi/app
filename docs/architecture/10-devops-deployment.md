# 14 & 15. DevOps & Deployment

[← Back to master](../ARCHITECTURE.md)

**Stack:** Docker · Docker Compose · Nginx · GitHub Actions · (Kubernetes/Helm-ready at scale).

## 14.1 Container topology

| Image | Base | Runs |
|-------|------|------|
| `api` | python:3.12-slim | Django DRF + Channels (Uvicorn workers under Gunicorn, ASGI) |
| `ai` | python:3.12 (+CUDA optional) | FastAPI AI service |
| `worker` | python:3.12-slim | Celery workers (per-queue: ingest, nlp, alerts, notify, ai, default) |
| `beat` | python:3.12-slim | Celery Beat scheduler |
| `web` | node:20 → nginx | Built RN Web / admin static bundle |
| `nginx` | nginx:alpine | Reverse proxy, TLS, gzip, rate-limit, static |
| `postgres` | timescale/timescaledb:pg16 | DB |
| `redis` | redis:7-alpine | cache/broker/channels |
| `opensearch` | opensearchproject/opensearch | search/logs |
| `minio` | minio/minio | object storage |

## 14.2 `docker-compose.yml` (dev shape)

```yaml
services:
  postgres: { image: timescale/timescaledb:latest-pg16, env_file: .env, volumes: [pgdata:/var/lib/postgresql/data], ports: ["5432:5432"] }
  redis:    { image: redis:7-alpine, ports: ["6379:6379"] }
  opensearch: { image: opensearchproject/opensearch:2, environment: [discovery.type=single-node], volumes: [osdata:/usr/share/opensearch/data] }
  minio:    { image: minio/minio, command: server /data --console-address ":9001", ports: ["9000:9000","9001:9001"], volumes: [miniodata:/data] }

  api:      { build: ./backend, command: gunicorn config.asgi -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000, env_file: .env, depends_on: [postgres, redis], ports: ["8000:8000"] }
  ai:       { build: ./ai_service, command: uvicorn app.main:app --host 0.0.0.0 --port 8100, env_file: .env, depends_on: [redis, minio] }
  worker:   { build: ./backend, command: celery -A config worker -Q ingest,nlp,alerts,notify,ai,default -l info, env_file: .env, depends_on: [redis, postgres] }
  beat:     { build: ./backend, command: celery -A config beat -l info, env_file: .env, depends_on: [redis] }
  nginx:    { image: nginx:alpine, volumes: ["./infra/nginx:/etc/nginx/conf.d"], ports: ["80:80","443:443"], depends_on: [api, ai] }

volumes: { pgdata: {}, osdata: {}, miniodata: {} }
```

Production splits compose files (`docker-compose.prod.yml`) and scales `api`/`worker`/`ai` replicas; secrets via Docker secrets / cloud secret manager, not `.env`.

## 14.3 Nginx responsibilities
TLS termination + HSTS, gzip/brotli, static asset serving, reverse proxy to `api` (HTTP + WebSocket upgrade) and `ai`, rate-limit zones, request size limits, security headers, IP allowlist for `/django-admin/`.

## 14.4 Environment variables (representative)
```
# Core
DJANGO_SETTINGS_MODULE, SECRET_KEY, DEBUG, ALLOWED_HOSTS, ENV
# DB / cache / search / storage
DATABASE_URL, REDIS_URL, OPENSEARCH_URL, MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
# Auth
JWT_PRIVATE_KEY, JWT_PUBLIC_KEY, ACCESS_TTL, REFRESH_TTL
GOOGLE_CLIENT_ID, APPLE_CLIENT_ID, APPLE_KEY
# AI service
AI_SERVICE_URL, AI_SERVICE_JWT_SECRET, ANTHROPIC_API_KEY, HF_TOKEN
# Providers
ALPHAVANTAGE_KEY, TWELVEDATA_KEY, FINNHUB_KEY, NEWSAPI_KEY, MARKETAUX_KEY, FRED_KEY
# Messaging / payments
FCM_KEY, APNS_KEY, TWILIO_*, TELEGRAM_BOT_TOKEN, WHATSAPP_*, SMTP_*
STRIPE_KEY, STRIPE_WEBHOOK_SECRET, RAZORPAY_KEY, RAZORPAY_SECRET
# Observability
SENTRY_DSN, OTEL_EXPORTER_OTLP_ENDPOINT
```
All typed via `django-environ`; `.env.example` committed, real `.env` gitignored.

## 14.5 CI/CD — GitHub Actions

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `ci-backend.yml` | PR/push | ruff/black/mypy → pytest (+coverage) → build image → trivy scan |
| `ci-frontend.yml` | PR/push | eslint/prettier/tsc → jest/RNTL → expo prebuild check |
| `ci-ai.yml` | PR/push | lint → pytest → model smoke tests |
| `security.yml` | PR + nightly | pip-audit, npm audit, trivy, secret scan (gitleaks) |
| `cd-staging.yml` | merge → main | build+push images → deploy staging → migrations → smoke tests |
| `cd-prod.yml` | tag/release | manual approval → rolling deploy → migrations → health checks → auto-rollback on failure |
| `mobile-build.yml` | tag | EAS build (iOS/Android) → submit to TestFlight/Play internal |

## 15. Deployment strategy
- **Migrations:** run as a pre-deploy job; backward-compatible (expand/contract) so rolling deploys never break.
- **Rollout:** rolling update with health/readiness probes; canary for AI model promotions (champion/challenger handled in-app, see [AI](06-ai-architecture.md)).
- **Rollback:** previous image tag kept; DB migrations designed reversible; model rollback = registry re-point (no redeploy).
- **Zero-downtime:** N+1 replicas, connection draining, sticky-free WS (Redis channel layer).
- **Scaling path:** Compose (v1, single/few hosts) → managed Kubernetes (HPA on CPU/RPS/queue-depth) with the same images + Helm chart; Postgres → managed + read replicas; Redis → cluster; OpenSearch → multi-node.

## 15.1 Observability
- **Logs:** structured JSON → shipped to OpenSearch (Filebeat/Fluent Bit); correlation via `X-Request-ID`.
- **Metrics:** Prometheus (django-prometheus, celery-exporter, node-exporter) → Grafana dashboards (RPS, latency, error rate, queue depth, ingestion lag, AI accuracy).
- **Tracing:** OpenTelemetry across API → AI → workers.
- **Errors:** Sentry (backend + RN).
- **Uptime:** external health checks (`/healthz`, `/readyz`) + alerting (PagerDuty/Slack).
- **Cost/quota:** `data_provider_status` tracks vendor quota; alerts before exhaustion → auto-failover.

## 15.2 Backups & DR
- Postgres: daily full + WAL/PITR; tested restores. MinIO: versioning + cross-region replication. Redis: AOF + snapshots (cache is rebuildable). OpenSearch: snapshot to MinIO/S3.
- RPO ≤ 15 min, RTO ≤ 1 hr targets; documented runbooks in [docs/deployment guide](../README.md).

## 15.3 Scheduled jobs (Celery Beat highlights)
| Job | Cadence | Queue |
|-----|---------|-------|
| Market quote poll (REST fallback) | 1–15s per tier | ingest |
| News poll all sources | 15–60s | ingest |
| Economic calendar sync | hourly | ingest |
| NLP reprocess backlog | continuous | nlp |
| Alert sweep (non-stream) | 10s | alerts |
| Nightly batch forecasts | daily off-peak | ai |
| Model drift evaluation | daily | ai |
| Partition maintenance / compression | daily | maintenance |
| OpenSearch reindex/refresh | as needed | maintenance |
| Digest notifications | daily/weekly | notify |
| Stale push-token cleanup | daily | maintenance |
