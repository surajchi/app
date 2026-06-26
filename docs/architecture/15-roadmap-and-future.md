# 17 & 18. Development Roadmap + Future Enhancements

[← Back to master](../ARCHITECTURE.md)

## 17. Development Roadmap

Phased, dependency-ordered. Each phase is independently shippable and maps to Claude Code build sessions (see master doc §1 build order).

### Phase 0 — Foundations (Weeks 1–2)
- Monorepo scaffold (`apps/`, `packages/`, `backend/`, `ai_service/`), tooling, lint/format/type configs.
- Docker Compose: Postgres+Timescale, Redis, OpenSearch, MinIO.
- Django project + settings split; core middleware, response envelope, exceptions, base models (`BaseModel`).
- Auth app: register/login/JWT/refresh rotation, email verify, password reset.
- CI skeleton (lint+test). README + dev guide.
- **Exit:** a user can sign up, log in, hit a health-checked authenticated endpoint.

### Phase 1 — Data model & reference data (Weeks 2–3)
- All migrations (identity, markets, news, portfolio, alerts, subscriptions, AI, ops).
- Seed scripts: countries, exchanges, sectors, instrument universe, symbol aliases.
- Django admin + RBAC roles/permissions seeded.
- **Exit:** schema matches ER; seeds load; admin can browse data.

### Phase 2 — Market data ingestion + realtime (Weeks 3–5)
- Integrations layer (anti-corruption) for 2–3 free providers + failover via `data_provider_status`.
- Tiered pollers (Celery beat) + normalizer + Redis latest + Timescale batched writes + continuous aggregates.
- Channels WebSocket gateway (JWT auth, subscribe/unsubscribe, fan-out).
- Stocks/forex/indices/commodities REST: list, detail, quote, history, indicators, movers, heatmap.
- **Exit:** live quotes stream to a test client; history + candles served; movers/heatmap precomputed.

### Phase 3 — News engine + NLP (Weeks 5–7)
- News integrations + RSS; dedup (URL hash + simhash); persistence + OpenSearch indexing.
- NLP pipeline (AI service): summarize, FinBERT sentiment, NER + entity linking, topic, impact scoring.
- News API (feed, detail, trending, personalized) + search/autocomplete.
- **Exit:** news flows source→enriched→indexed→queryable; entity-linked to instruments.

### Phase 4 — AI service core (Weeks 7–10)
- FastAPI scaffold, model registry (MinIO), feature engineering pipeline.
- Forecasting (start Prophet/ARIMA/XGBoost → add LSTM/GRU/Transformer ensemble), sentiment endpoint, technical/indicator engine, risk, pattern (v1 rule-based), confidence scoring.
- Training pipeline + `training_jobs` + champion/challenger promotion; nightly batch forecasts.
- Django `/ai/*` proxy with entitlements + caching + `ai_predictions` persistence.
- **Exit:** forecasts/sentiment/TA available via API with confidence + disclaimer; models versioned & promotable.

### Phase 5 — Notification engine (Weeks 9–11, overlaps)
- Multi-channel dispatchers (push/email/SMS/telegram/whatsapp/in-app), priority queues, retry/offline queue.
- Alert engine: rule evaluation against quote stream + news entities + economic events; cooldown/dedupe.
- Preferences + quiet hours + inbox API.
- **Exit:** price/news/economic alerts fire end-to-end within SLA; preferences respected.

### Phase 6 — Frontend foundation (Weeks 6–10, parallel track)
- Expo app shell, navigation, theme tokens + dark mode, i18n, providers, secure auth flows (incl. Google/Apple/OTP/2FA).
- Dashboard, markets list/detail with live charts, search.
- **Exit:** user can log in, browse markets, view a live candlestick chart on iOS/Android/Web.

### Phase 7 — Feature build-out (Weeks 10–14)
- Watchlists, portfolio (holdings, P&L, performance), alerts UI, news feed, AI insights/forecasts screens, economic calendar, saved charts/searches, bookmarks, profile/settings.
- **Exit:** all core user features usable across platforms.

### Phase 8 — Subscriptions, payments, admin (Weeks 14–17)
- Plans/entitlements, Stripe + Razorpay + IAP, webhooks, invoices.
- Admin panel (users, RBAC, market/news/model mgmt, broadcasts, feature flags, billing, audit, analytics).
- **Exit:** users can subscribe; admins can operate the platform.

### Phase 9 — Hardening (Weeks 17–20)
- Security pass (headers, rate limits, pentest fixes, secret rotation), full test coverage, observability (logs/metrics/traces/Sentry), load testing to scale targets, DR drills.
- **Exit:** meets scale + security + reliability targets.

### Phase 10 — Polish & launch (Weeks 20–22)
- A11y, performance tuning, store assets, EAS builds, TestFlight/Play submission, docs finalization, soft launch + monitoring.
- **Exit:** public launch.

> Timeline assumes a small senior team; with Claude Code-driven sessions, many phases compress. Phases 2–6 can run in parallel tracks (data/AI vs frontend).

## MVP cut (fastest credible launch)
Auth + markets (stocks/forex) live quotes & charts + watchlists + news feed with sentiment + basic price alerts (push) + one forecast model (Prophet/XGBoost) + free plan only. Defer: portfolio analytics, full AI suite, all payment providers, full admin, multi-language.

---

## 18. Future Enhancements

| Area | Enhancement |
|------|-------------|
| **Crypto** | Activate `cryptocurrencies`/`crypto_prices` + exchange integrations (schema already present, feature-flagged). |
| **Trading/Orders** | Activate `orders` with broker integrations (Kite/Upstox/Alpaca/IBKR) for real execution + paper trading. |
| **Options & derivatives** | Option chains, greeks, strategy builder, F&O analytics (NSE F&O). |
| **Social / community** | Follow analysts, share ideas/charts, sentiment crowd-index, leaderboards, copy-watchlists. |
| **Advanced AI** | Multi-agent research assistant, auto-generated daily briefings per portfolio, scenario simulation, RL-based strategy backtesting, fine-tuned domain LLM. |
| **Backtesting platform** | User-defined strategies tested on historical data with the same indicator engine. |
| **Screeners 2.0** | Natural-language screeners ("show me oversold large-cap IT stocks with positive news"). |
| **Voice & widgets** | Voice assistant, home-screen widgets, watch apps, Siri/Google shortcuts. |
| **Alternative data** | Earnings-call transcripts + sentiment, insider/institutional flows, supply-chain/ESG signals. |
| **Internationalization** | More languages + RTL, region-specific tax/portfolio reports, localized compliance. |
| **Enterprise / API product** | Public partner API (we already model `api_keys`/scopes), white-label, B2B data feeds. |
| **Infra at scale** | Kubernetes + Helm, service mesh, multi-region active-active, edge caching for quotes, gRPC internal transport. |
| **ML Ops** | Feature store, automated retraining + drift-triggered pipelines, A/B testing of models, model cards & governance. |
| **Compliance** | SEBI/RBI/GDPR/DPDP certifications, SOC 2, audit-ready reporting, data residency per region. |
| **Monetization** | Tiered AI credits, pay-per-report, affiliate broker referrals, premium data add-ons. |
