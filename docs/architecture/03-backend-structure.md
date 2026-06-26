# 4. Backend Structure

[← Back to master](../ARCHITECTURE.md)

**Stack:** Python 3.12 · Django 5 · Django REST Framework · Django Channels · Celery · FastAPI (AI service) · PostgreSQL + TimescaleDB · Redis · OpenSearch · MinIO.

**Pattern:** Clean-ish layered architecture inside each Django app — `models → repositories → services → serializers → views/urls` — plus a separate FastAPI service for ML.

## 4.1 Repository layout

```
backend/
├── manage.py
├── pyproject.toml / requirements/        # base.txt, dev.txt, prod.txt, ai.txt
├── config/                               # Django project (settings package)
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py  dev.py  staging.py  prod.py
│   │   └── test.py
│   ├── asgi.py                           # Channels + DRF (ASGI)
│   ├── wsgi.py
│   ├── urls.py                           # /api/v1 router include
│   └── celery.py                         # Celery app
│
├── apps/                                 # ★ feature apps (Django apps)
│   ├── authentication/                   # login, JWT, OAuth, OTP, 2FA, sessions, devices
│   ├── users/                            # user model, RBAC roles/permissions
│   ├── profiles/                         # profile, preferences, KYC-lite
│   ├── markets/                          # shared market metadata
│   │   ├── forex/
│   │   ├── stocks/
│   │   ├── commodities/
│   │   ├── indices/
│   │   ├── etfs/
│   │   └── crypto/
│   ├── news/                             # news models + pipeline orchestration
│   ├── economic_calendar/
│   ├── portfolio/
│   ├── watchlists/
│   ├── alerts/                           # alert rules + evaluation
│   ├── notifications/                    # multi-channel delivery
│   ├── subscriptions/                    # plans, entitlements
│   ├── payments/                         # PSP integration, invoices
│   ├── recommendations/                  # rec engine glue (calls AI service)
│   ├── analytics/                        # product analytics, usage events
│   ├── admin_panel/                      # admin-only APIs (distinct from Django /admin)
│   └── ai/                               # Django-side AI proxy (calls FastAPI), predictions store
│
├── core/                                 # cross-cutting framework code
│   ├── middleware/                       # request id, rate limit, audit, security headers
│   ├── permissions/                      # DRF permission classes (RBAC, ownership, plan)
│   ├── pagination/
│   ├── throttling/
│   ├── exceptions/                       # custom handlers, error envelope
│   ├── renderers/                        # standard response envelope
│   ├── repositories/                     # base repository (query abstraction)
│   ├── services/                         # base service, unit-of-work
│   ├── cache/                            # redis cache helpers, decorators
│   ├── events/                           # domain events / Redis Streams helpers
│   └── feature_flags/
│
├── common/                               # shared utils & value objects
│   ├── utils/                            # money, tz, symbols, hashing
│   ├── validators/
│   ├── enums.py
│   ├── constants.py
│   └── mixins.py                         # TimeStamped, SoftDelete, UUIDPk models
│
├── websocket/                            # Channels consumers & routing
│   ├── routing.py
│   ├── consumers/                        # quotes, news, alerts, portfolio
│   ├── middleware.py                     # JWT auth for WS
│   └── channel_layers.py
│
├── integrations/                         # external API clients (anti-corruption layer)
│   ├── market_data/                      # alphavantage, twelvedata, finnhub, yahoo…
│   ├── indian_market/                    # nse, bse adapters
│   ├── news/                             # newsapi, gnews, rss, marketaux…
│   ├── economic/                         # tradingeconomics, fred…
│   ├── payments/                         # stripe, razorpay
│   ├── oauth/                            # google, apple
│   ├── messaging/                        # fcm, apns, twilio, telegram, whatsapp, smtp
│   └── base.py                           # retry, circuit breaker, rate-limit, caching
│
├── tasks/                                # Celery tasks grouped by domain
│   ├── ingestion/                        # market & news pollers
│   ├── nlp/                              # sentiment, summarize, NER orchestration
│   ├── alerts/                           # rule evaluation
│   ├── notifications/                    # dispatch + retry
│   ├── ai/                               # training triggers, batch inference
│   ├── maintenance/                      # cleanup, partition mgmt, reindex
│   └── schedules.py                      # Celery beat schedule registry
│
├── search/                               # OpenSearch layer
│   ├── indices/                          # index definitions/mappings
│   ├── documents/                        # serialization to docs
│   ├── queries/                          # query builders
│   └── client.py
│
├── scripts/                              # ops & dev scripts
│   ├── seed/                             # seed markets, symbols, demo data
│   ├── backfill/                         # historical data backfill
│   └── manage_partitions.py
│
└── tests/                                # project-level integration/e2e tests
    ├── integration/
    ├── e2e/
    ├── load/                             # locust/k6 scripts
    └── factories/                        # factory_boy fixtures
```

### Separate AI service

```
ai_service/                               # FastAPI (own container, own deps: ai.txt)
├── app/
│   ├── main.py                           # FastAPI app, routers, middleware
│   ├── api/
│   │   ├── v1/
│   │   │   ├── forecast.py
│   │   │   ├── sentiment.py
│   │   │   ├── technical.py
│   │   │   ├── patterns.py
│   │   │   ├── risk.py
│   │   │   ├── recommend.py
│   │   │   └── assistant.py              # LLM chat assistant
│   │   └── deps.py                       # auth (service JWT), model registry
│   ├── models/                           # model wrapper classes
│   │   ├── forecasting/                  # lstm, gru, transformer, prophet, arima, xgboost
│   │   ├── nlp/                          # finbert, sentence-transformers, ner, topic
│   │   ├── technical/                    # indicator engine, pattern detectors
│   │   └── registry.py                   # load/cache versioned models from MinIO
│   ├── pipelines/                        # training & inference pipelines
│   │   ├── training/
│   │   ├── inference/
│   │   └── features/                     # feature engineering (shared)
│   ├── schemas/                          # pydantic request/response
│   ├── core/                             # config, logging, cache, metrics
│   └── services/
├── notebooks/                            # research (not deployed)
├── tests/
└── requirements.txt

ai_models/                                # versioned model artifacts (synced to MinIO)
├── forecasting/
├── nlp/
└── registry.json                         # model → version → metrics → uri
```

## 4.2 Layering inside a Django app (example: `apps/markets/stocks`)

```
stocks/
├── __init__.py
├── apps.py
├── models.py                  # Stock, StockPrice (hypertable), Company FK…
├── repositories.py            # StockRepository (all ORM queries live here)
├── services.py                # StockService (business logic, caching, orchestration)
├── selectors.py               # read-optimized query functions
├── serializers.py             # DRF serializers (in/out DTOs)
├── views.py                   # DRF ViewSets / APIViews (thin)
├── urls.py
├── tasks.py                   # Celery tasks specific to stocks
├── signals.py                 # post_save → search index, cache bust
├── permissions.py             # feature/plan gates
├── filters.py                 # django-filter querysets
├── constants.py
├── admin.py                   # Django admin registration
└── tests/
    ├── test_models.py
    ├── test_repositories.py
    ├── test_services.py
    └── test_api.py
```

### Layer rules (enforced in code review / CI lint)
1. **Views** never touch the ORM directly → call **services/selectors**.
2. **Services** hold business logic, transactions, and call **repositories** + **integrations** + cache.
3. **Repositories** are the only place with ORM `.objects` query construction (Repository Pattern).
4. **Serializers** validate I/O only — no business logic.
5. **Integrations** are the only place that talks to the outside world (anti-corruption layer with retry/circuit-breaker).
6. Cross-app calls go through a service's **public interface**, never another app's repository.

## 4.3 Base building blocks (in `core/` and `common/`)

```python
# common/mixins.py
class UUIDPrimaryKeyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    class Meta: abstract = True

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True

class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    objects = SoftDeleteManager()      # default: excludes deleted
    all_objects = models.Manager()     # includes deleted
    def soft_delete(self): self.deleted_at = timezone.now(); self.save(update_fields=["deleted_at"])
    class Meta: abstract = True

class BaseModel(UUIDPrimaryKeyModel, TimeStampedModel, SoftDeleteModel):
    class Meta: abstract = True
```

Every domain table inherits `BaseModel` → consistent UUID PK, `created_at`, `updated_at`, soft delete.

## 4.4 Standard API response envelope

```jsonc
// success
{ "success": true, "data": { ... }, "meta": { "page": 1, "page_size": 20, "total": 153 } }
// error
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "…", "details": { "field": ["…"] } } }
```

Implemented via a custom DRF **renderer** + **exception handler** in `core/renderers` and `core/exceptions`.

## 4.5 Async vs sync
- DRF runs under **ASGI** (Uvicorn workers behind Gunicorn) so it shares the process model with Channels.
- CPU/IO-heavy and scheduled work → **Celery** (never block request threads).
- AI inference → **HTTP call to FastAPI** (sync for interactive, async via Celery for batch).

## 4.6 Configuration & secrets
- `django-environ` for typed env vars; **no secrets in code**.
- Secrets from environment (injected by Docker secrets / Vault / cloud secret manager).
- Settings split per environment (`config/settings/*`).
