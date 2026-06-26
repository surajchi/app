# FinPulse — AI-Powered Forex & Global Market Intelligence Platform
## Master Architecture Document (v1.0)

> Status: **Blueprint / Pre-implementation** · Owner: `owner@shubhamtanks.com` · Date: 2026-06-26
>
> This is the master blueprint. It is intentionally exhaustive so it can be converted into code over multiple development sessions with Claude Code. Each numbered section below is also available as a standalone file under [`docs/architecture/`](architecture/) for deep work.

---

## How to read this document

| # | Section | Standalone file |
|---|---------|-----------------|
| 1 | Executive Summary | (this file) |
| 2 | High-Level Architecture | [01-high-level-architecture.md](architecture/01-high-level-architecture.md) |
| 3 | Frontend Folder Structure | [02-frontend-structure.md](architecture/02-frontend-structure.md) |
| 4 | Backend Structure | [03-backend-structure.md](architecture/03-backend-structure.md) |
| 5 | Database Schema | [04-database-schema.md](architecture/04-database-schema.md) |
| 6 | ER Diagram (Mermaid) | [04-database-schema.md](architecture/04-database-schema.md) |
| 7 | API Design | [05-api-design.md](architecture/05-api-design.md) |
| 8 | AI Architecture | [06-ai-architecture.md](architecture/06-ai-architecture.md) |
| 9 | Notification Architecture | [07-notifications.md](architecture/07-notifications.md) |
| 10 | Authentication | [08-auth-and-security.md](architecture/08-auth-and-security.md) |
| 11 | User Management | [08-auth-and-security.md](architecture/08-auth-and-security.md) |
| 12 | Admin Panel | [09-admin-panel.md](architecture/09-admin-panel.md) |
| 13 | Security | [08-auth-and-security.md](architecture/08-auth-and-security.md) |
| 14–15 | DevOps & Deployment | [10-devops-deployment.md](architecture/10-devops-deployment.md) |
| 16 | Testing Strategy | [11-testing.md](architecture/11-testing.md) |
| — | Market Data, News, Charts, Search | [12-data-engines.md](architecture/12-data-engines.md) |
| — | Free Data Sources | [13-data-sources.md](architecture/13-data-sources.md) |
| — | Coding Standards | [14-coding-standards.md](architecture/14-coding-standards.md) |
| 17 | Development Roadmap | [15-roadmap-and-future.md](architecture/15-roadmap-and-future.md) |
| 18 | Future Enhancements | [15-roadmap-and-future.md](architecture/15-roadmap-and-future.md) |

---

## 1. Executive Summary

### 1.1 Product vision
**FinPulse** is an AI-powered financial intelligence platform that delivers the **fastest possible market news**, **live multi-asset market data**, and **AI-generated analysis & forecasting** to retail and prosumer investors across **Web, Android, and iOS** from a single React Native + Expo codebase.

It blends the live-charting experience of **TradingView**, the breadth of **Investing.com / Trading Economics**, the news velocity of **Google News**, and the conversational analysis of an **LLM assistant** — into one product.

### 1.2 Asset classes covered
Forex · Indian equities (NSE & BSE) · US equities · European markets · Commodities · ETFs · Indices · Crypto (future-ready, schema and ingestion designed in from day one).

### 1.3 Core capabilities

| Pillar | What it does |
|--------|--------------|
| **Real-time market data** | Live quotes, OHLC/candles, order-book-lite, market movers, heatmaps, sector performance over WebSocket. |
| **News engine** | Multi-source ingestion → dedup → categorize → summarize → sentiment (FinBERT) → impact scoring → entity extraction → push within seconds. |
| **AI engine** | Price forecasting (LSTM/GRU/Transformer/Prophet/ARIMA/XGBoost), sentiment, technical analysis, pattern recognition, risk scoring, historical analogs, and an LLM market assistant. |
| **Personalization** | Watchlists, portfolios, custom alert rules, saved charts/searches, recommendations. |
| **Notifications** | Push, Email, SMS, Telegram, WhatsApp, desktop — priority-tiered, retried, offline-queued. |
| **Admin** | Full operational control plane: users, RBAC, market/news/model management, feature flags, billing, audit. |

### 1.4 Architectural stance (the 7 principles)

1. **Polyglot but bounded** — Django (DRF + Channels + Celery) owns product/business APIs and real-time; **FastAPI** owns AI inference (own scaling profile, GPU-friendly). Clear contract between them.
2. **Event-driven core** — ingestion, scoring, and notifications flow through Redis Streams / Celery so the system degrades gracefully and scales horizontally.
3. **Read-optimized** — heavy fan-out reads (quotes, news, charts) are served from Redis + OpenSearch caches, never from hot OLTP paths.
4. **Time-series aware** — price data lives in partitioned/TimescaleDB-style tables tuned for range scans; product data lives in normalized PostgreSQL.
5. **Feature-based modularity** — both frontend and backend are organized by *feature*, not by *file type*, so teams and AI agents can own vertical slices.
6. **Stateless services, stateful stores** — every service is horizontally scalable; all state in Postgres/Redis/MinIO/OpenSearch.
7. **Future-ready, not future-built** — crypto, options/orders, and social are modeled in the schema but feature-flagged off until built.

### 1.5 Scale targets (design envelope)

| Metric | Target |
|--------|--------|
| Registered users | 10M |
| Concurrent WebSocket connections | 500k+ |
| Quote update fan-out | 100k+ symbols/sec aggregate |
| News-to-notification latency (p95) | < 5s from source publish |
| API p99 latency (cached reads) | < 150ms |
| AI inference p95 (cached) | < 300ms; (cold forecast) < 3s |
| Availability | 99.9% |

### 1.6 Non-goals (v1)
- We are **not** a broker/exchange — no real order execution in v1 (orders table exists, feature-flagged).
- No proprietary low-latency market-making feed; we consume vendor/free APIs.
- Not financial advice — all AI output is decorated with disclaimers and confidence scores.

### 1.7 Compliance & disclaimer posture
- Every AI prediction/recommendation carries a **confidence score** and a non-advice disclaimer.
- PII encrypted at rest; payment data tokenized via PSP (we never store PANs).
- Region-aware data residency hooks (esp. for Indian users — SEBI/RBI sensitivity).
- Full audit trail on every privileged action.

---

## 2–18

See the linked standalone files in the table above. Start with [01-high-level-architecture.md](architecture/01-high-level-architecture.md) and follow the build order in [15-roadmap-and-future.md](architecture/15-roadmap-and-future.md).

### Suggested implementation order for Claude Code sessions
1. **Session 1 — Foundations:** repo scaffold (monorepo), Docker Compose, Postgres + Redis + base Django project, auth app, CI skeleton. (§3, §4, §8, §10)
2. **Session 2 — Data model:** all migrations, ER-verified schema, seed scripts, admin registration. (§5)
3. **Session 3 — Market data ingestion:** integrations layer, Celery beat schedules, WebSocket fan-out, charts API. (§ data-engines)
4. **Session 4 — News pipeline:** ingestion → NLP → store → notify. (§ data-engines, §9)
5. **Session 5 — AI service:** FastAPI scaffold, forecasting + sentiment endpoints, model registry. (§6)
6. **Session 6 — Frontend foundation:** Expo app shell, navigation, theme, auth flows, dashboard. (§3)
7. **Session 7 — Feature build-out:** markets, watchlists, portfolio, alerts, news feed, AI insights screens.
8. **Session 8 — Admin panel + payments + subscriptions.** (§9)
9. **Session 9 — Hardening:** security, testing, observability, load testing. (§ security, §11, §10)
10. **Session 10 — Polish & launch:** i18n, dark mode, store submission, docs.
