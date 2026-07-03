# FinPulse — AI-Powered Forex & Global Market Intelligence Platform

> The fastest financial news, live multi-asset market data, and AI-generated analysis & forecasting — Web, Android, iOS — from one codebase.

TradingView + Bloomberg-lite + Investing.com + Trading Economics + Google News + an LLM market assistant, engineered for millions of users.

## What's here

A working, monorepo implementation of the FinPulse platform — Django/DRF backend
(REST + WebSockets + Celery), a FastAPI AI microservice, and an Expo (iOS /
Android / Web) client — built on the architecture blueprint in [`docs/`](docs/).
Everything runs **free of paid third-party APIs**: market data, news, sentiment,
AI, and payments all default to self-contained providers, swappable via env vars.

📐 **Architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · 🐳 **Docker (Windows):** [`docs/DOCKER.md`](docs/DOCKER.md) · 🚀 **Deploy:** [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

### Build status

| Phase | Scope | Status |
|-------|-------|--------|
| 1  | Monorepo + foundation (settings, health, logging, CI) | ✅ |
| 2  | Auth, users, RBAC, profiles, sessions & devices, OAuth/OTP/2FA | ✅ |
| 3  | Market data + WebSockets + historical (TimescaleDB) | ✅ |
| 4  | News ingestion + NLP + sentiment + search | ✅ |
| 5  | AI engine (forecasting, technical, recommendations) | ✅ |
| 6  | Notifications + alert engine | ✅ |
| 7  | Watchlists, portfolio, dashboard (+ mobile screens) | ✅ |
| 8  | Admin console (RBAC-gated, audit log) | ✅ |
| 9  | Payments & subscriptions (pluggable provider) | ✅ |
| 10 | Hardening, docs, deployment | ✅ |

### Run it (local, Docker)

```bash
cp backend/.env.example backend/.env
docker compose up -d                       # api, worker, beat, ai, postgres, redis, …
docker compose run --rm api python manage.py createsuperuser
# API docs: http://localhost:8000/api/docs/   ·   health: /healthz/  /readyz/

# Mobile / web client
cp apps/mobile/.env.example apps/mobile/.env
pnpm install && pnpm --filter @finpulse/mobile web
```

Backend gate (lint + types + tests): `docker compose run --rm api sh -c "ruff check . && black --check . && mypy . && pytest -q"`.

| Topic | Doc |
|-------|-----|
| Executive summary & build order | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Docker setup & usage (Windows) | [docs/DOCKER.md](docs/DOCKER.md) |
| High-level architecture | [docs/architecture/01-high-level-architecture.md](docs/architecture/01-high-level-architecture.md) |
| Frontend structure | [docs/architecture/02-frontend-structure.md](docs/architecture/02-frontend-structure.md) |
| Backend structure | [docs/architecture/03-backend-structure.md](docs/architecture/03-backend-structure.md) |
| Database schema + ER diagram | [docs/architecture/04-database-schema.md](docs/architecture/04-database-schema.md) |
| API design | [docs/architecture/05-api-design.md](docs/architecture/05-api-design.md) |
| AI architecture | [docs/architecture/06-ai-architecture.md](docs/architecture/06-ai-architecture.md) |
| Notifications | [docs/architecture/07-notifications.md](docs/architecture/07-notifications.md) |
| Auth, users & security | [docs/architecture/08-auth-and-security.md](docs/architecture/08-auth-and-security.md) |
| Admin panel | [docs/architecture/09-admin-panel.md](docs/architecture/09-admin-panel.md) |
| DevOps & deployment | [docs/architecture/10-devops-deployment.md](docs/architecture/10-devops-deployment.md) |
| Testing strategy | [docs/architecture/11-testing.md](docs/architecture/11-testing.md) |
| Data engines (market/news/charts/search) | [docs/architecture/12-data-engines.md](docs/architecture/12-data-engines.md) |
| Free data sources | [docs/architecture/13-data-sources.md](docs/architecture/13-data-sources.md) |
| Coding standards | [docs/architecture/14-coding-standards.md](docs/architecture/14-coding-standards.md) |
| Roadmap & future | [docs/architecture/15-roadmap-and-future.md](docs/architecture/15-roadmap-and-future.md) |

## Tech stack (summary)

- **Frontend:** React Native · Expo · React Native Web · TypeScript · Zustand · React Query · React Navigation · React Hook Form · NativeWind · Reanimated · Victory · RN SVG
- **Backend:** Python · Django · DRF · Channels · Celery
- **AI:** FastAPI · PyTorch · TensorFlow · HuggingFace/Transformers · scikit-learn · XGBoost · Prophet · pandas · NumPy
- **Data:** PostgreSQL (+TimescaleDB) · Redis · OpenSearch · MinIO
- **Infra:** Docker · Docker Compose · Nginx · GitHub Actions

## Planned repository layout

```
finpulse/
├── apps/
│   ├── mobile/          # Expo app → iOS, Android, Web
│   └── admin/           # Admin dashboard
├── packages/            # ui, api-client, types, config (shared)
├── backend/             # Django + DRF + Channels + Celery
├── ai_service/          # FastAPI ML service
├── ai_models/           # Versioned model artifacts (synced to MinIO)
├── infra/               # nginx, compose overrides, k8s/helm (later)
├── docs/                # this blueprint
└── docker-compose.yml
```

## Quickstart (once code exists — target shape)

```bash
# Backend + frontend env live in their own folders:
cp backend/.env.example backend/.env          # backend + infra config/secrets
cp apps/mobile/.env.example apps/mobile/.env   # EXPO_PUBLIC_* only

docker compose up -d          # postgres, redis, opensearch, minio, api, worker, beat
# (api auto-runs collectstatic + migrate on start)
# API docs:  http://localhost:8000/api/docs/
# MinIO:     http://localhost:9001
```

Mobile/web app:
```bash
pnpm install
pnpm --filter @finpulse/mobile web   # or: start (then press i / a / w)
```

## Status
🟡 **Blueprint phase** — no application code yet. Follow the build order in [docs/ARCHITECTURE.md §1](docs/ARCHITECTURE.md).

## Disclaimer
FinPulse provides market data and AI-generated analysis for **informational purposes only**. Nothing in the product constitutes financial advice. AI outputs include confidence scores and may be inaccurate.

---
*Architecture blueprint generated as the master plan for implementation with Claude Code.*
