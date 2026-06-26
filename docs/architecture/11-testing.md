# 16. Testing Strategy

[← Back to master](../ARCHITECTURE.md)

Test pyramid: many fast unit tests, fewer integration tests, few end-to-end. Plus specialized AI-model and load tests. CI gates merges on lint + type + tests + coverage threshold.

## 16.1 Backend (Django/DRF + Celery)

| Type | Tooling | Scope |
|------|---------|-------|
| **Unit** | pytest, pytest-django, factory_boy | services, repositories, selectors, utils, serializers (isolated, mocked I/O) |
| **Integration** | pytest + test Postgres + fakeredis/real redis | repository↔DB, Celery tasks (eager mode), cache, search via test OpenSearch |
| **API** | DRF APIClient / pytest | endpoint contracts, auth/permissions, validation, pagination, error envelope |
| **WebSocket** | Channels `WebsocketCommunicator` | subscribe/auth/fan-out behavior |
| **Contract** | schemathesis against OpenAPI | request/response schema conformance |
| **Migration** | `makemigrations --check`, migration tests | no missing/destructive migrations; reversibility |

Coverage target: **≥ 85%** on services/repositories; permissions and auth flows near 100%.

## 16.2 AI service (FastAPI + models)

| Type | Scope |
|------|-------|
| **Unit** | feature engineering (train/serve parity), schema validation, registry load |
| **Model quality** | metric thresholds on held-out set (RMSE/MAE/MAPE, directional acc, F1) — CI fails if a candidate underperforms baseline |
| **Inference smoke** | each endpoint returns valid shape + confidence + disclaimer for sample instruments |
| **Drift tests** | data/concept drift detectors validated on synthetic shifts |
| **Determinism** | seeded inference reproducibility |
| **Backtesting** | walk-forward backtest harness for forecast/signal models |

## 16.3 Frontend (React Native / RN Web)

| Type | Tooling | Scope |
|------|---------|-------|
| **Unit** | Jest | utils, hooks (incl. React Query hooks w/ MSW), store slices, formatters |
| **Component** | React Native Testing Library | components render/interaction, forms (RHF+Zod) |
| **Integration** | RNTL + MSW (mock API/WS) | screen flows (login, watchlist add, alert create) |
| **E2E** | Detox (mobile) / Playwright (web) | critical journeys: onboarding, view chart, set alert, subscribe |
| **Visual/a11y** | Storybook + accessibility checks | design-system regressions, a11y |
| **Type** | tsc strict | no `any`, no implicit |

## 16.4 Performance & load

| Test | Tooling | Target |
|------|---------|--------|
| API load | k6 / Locust | p99 < 150ms cached reads at target RPS; graceful 429 under spike |
| WebSocket fan-out | custom k6 ws / artillery | 100k+ concurrent connections per cluster; quote frame latency p95 |
| Ingestion throughput | bench harness | sustain target ticks/sec without queue growth |
| DB | pgbench + EXPLAIN review | hot queries indexed; no seq scans on hot paths |
| Soak | k6 long-run | no memory leaks / queue drift over 24h |

## 16.5 Security testing
- SAST (CodeQL), dependency audit (pip-audit/npm audit/Dependabot), container scan (trivy), secret scan (gitleaks) in CI.
- DAST (OWASP ZAP) against staging; periodic manual pentest; auth fuzzing on token/OTP flows.

## 16.6 Test data & environments
- `factories/` (factory_boy) for deterministic fixtures; seed scripts for markets/symbols.
- Ephemeral test DB per CI run; MSW for frontend network mocking; recorded provider fixtures (VCR.py) for integration adapters so tests don't hit live vendor APIs.
- Staging mirrors prod with synthetic + anonymized data for E2E and load.

## 16.7 Quality gates (CI)
PR cannot merge unless: lint+format clean, type-check passes, unit+integration green, coverage ≥ threshold, no high/critical vulns, OpenAPI contract valid, migrations check passes.
