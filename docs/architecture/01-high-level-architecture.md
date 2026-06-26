# 2. High-Level Architecture

[← Back to master](../ARCHITECTURE.md)

## 2.1 System context (C4 — Level 1)

```mermaid
graph TB
    subgraph Clients
        MOB[Mobile App<br/>iOS / Android<br/>React Native + Expo]
        WEB[Web App<br/>React Native Web]
        ADM[Admin Dashboard<br/>Web]
    end

    subgraph Edge
        CDN[CDN / Static assets]
        LB[Nginx / Load Balancer<br/>TLS termination, rate limit]
    end

    subgraph Platform
        API[Django + DRF<br/>REST API]
        WS[Django Channels<br/>WebSocket Gateway]
        AI[FastAPI<br/>AI Inference Service]
        WORK[Celery Workers<br/>+ Beat]
    end

    subgraph Stores
        PG[(PostgreSQL<br/>+ TimescaleDB)]
        RDS[(Redis<br/>cache / streams / pubsub)]
        OS[(OpenSearch)]
        MIN[(MinIO<br/>S3-compatible)]
    end

    subgraph External
        MKT[Market Data APIs]
        NEWS[News APIs]
        ECON[Economic Calendar APIs]
        PSP[Payment Gateways]
        OAUTH[Google / Apple OAuth]
        CH[Notification Channels<br/>FCM/APNs/Email/SMS/Telegram/WhatsApp]
    end

    MOB & WEB & ADM --> CDN
    MOB & WEB & ADM --> LB
    LB --> API
    LB --> WS
    API --> PG & RDS & OS
    API --> AI
    WS --> RDS
    WORK --> PG & RDS & OS & MIN
    WORK --> AI
    AI --> PG & RDS & MIN
    WORK --> MKT & NEWS & ECON
    API --> PSP & OAUTH
    WORK --> CH
    WS -. fan-out .- RDS
```

## 2.2 Component responsibilities

| Component | Tech | Responsibility | Scaling profile |
|-----------|------|----------------|-----------------|
| **API Service** | Django + DRF (ASGI via Uvicorn/Gunicorn) | Auth, business logic, CRUD, orchestration, serving cached reads | Stateless, horizontal (HPA on CPU/RPS) |
| **WebSocket Gateway** | Django Channels (ASGI) + Redis channel layer | Live quote/news/alert push to clients | Horizontal; sticky not required (Redis pub/sub) |
| **AI Service** | FastAPI + PyTorch/TF/sklearn | Forecasting, sentiment, TA, pattern, recommendation inference | Horizontal; GPU node pool optional; model cache |
| **Workers** | Celery (Redis broker) + Beat | Ingestion, NLP pipeline, scheduled jobs, notification dispatch, model training triggers | Horizontal by queue; priority queues |
| **PostgreSQL** | PG 16 + TimescaleDB ext | OLTP product data + time-series price data | Primary + read replicas; partitioning |
| **Redis** | Redis 7 (cluster) | Cache, Celery broker, Channels layer, Streams, rate-limit counters, pub/sub | Cluster mode, replicas |
| **OpenSearch** | OpenSearch | Full-text search (companies/news/symbols), autocomplete, log analytics | Multi-node cluster |
| **MinIO** | MinIO | Model artifacts, exported reports, chart snapshots, user uploads | Distributed mode |

## 2.3 Why Django + FastAPI split

| Concern | Owner | Reason |
|---------|-------|--------|
| Auth, RBAC, CRUD, billing, admin | **Django** | Batteries-included ORM, admin, mature auth, DRF serializers |
| Real-time fan-out | **Django Channels** | Native ASGI + Redis channel layer, shares models |
| Background jobs | **Celery** | First-class Django integration |
| ML inference & training | **FastAPI** | Lightweight, async, easy to pin to GPU pods, isolated deps (torch/tf), independent deploy cadence, no Django request overhead |

The two communicate via **internal REST (signed service-to-service JWT)** for synchronous inference and **Redis Streams / Celery** for async (e.g., bulk news sentiment).

## 2.4 Data flow — market data (real-time path)

```mermaid
sequenceDiagram
    participant V as Vendor API/WS
    participant ING as Ingestor (Celery/asyncio)
    participant N as Normalizer
    participant R as Redis (cache + stream)
    participant TS as TimescaleDB
    participant WS as Channels Gateway
    participant C as Client

    V->>ING: raw tick / quote
    ING->>N: normalize (symbol map, currency, tz)
    N->>R: SET latest:{symbol} (TTL) + XADD ticks stream
    N->>TS: async batch insert OHLC/ticks
    R-->>WS: pub/sub channel quotes.{symbol}
    WS-->>C: push quote frame (only subscribed symbols)
```

Key design points:
- Clients **subscribe** to specific channels (`quotes.AAPL`, `news.IN`, `alerts.{userId}`) — server never broadcasts everything.
- Latest-quote reads come from Redis (`O(1)`), historical from TimescaleDB hypertables.
- Writes to TS are **batched** (e.g., 250ms or 500-row windows) to protect the DB.

## 2.5 Data flow — news (fastest-notification path)

```mermaid
sequenceDiagram
    participant SRC as News sources (APIs/RSS/scrapers)
    participant POLL as Poller (Celery beat, short interval)
    participant DEDUP as Dedup (simhash + URL canon)
    participant NLP as NLP pipeline (FastAPI/worker)
    participant DB as Postgres + OpenSearch
    participant NOTIF as Notification engine
    participant U as Users

    POLL->>DEDUP: raw articles
    DEDUP->>NLP: unique articles
    NLP->>NLP: categorize, summarize, FinBERT sentiment,<br/>impact score, NER entities
    NLP->>DB: persist + index
    NLP->>NOTIF: high-impact event (entity match → user rules)
    NOTIF->>U: push/email/telegram (priority-tiered)
```

## 2.6 Deployment topology (logical)

```mermaid
graph LR
    subgraph "Edge tier"
        NGINX[Nginx Ingress<br/>TLS, rate-limit, gzip]
    end
    subgraph "App tier (stateless, autoscaled)"
        A1[API pods]
        W1[WS pods]
        AI1[AI pods]
    end
    subgraph "Worker tier"
        C1[Celery default]
        C2[Celery ingest]
        C3[Celery nlp]
        C4[Celery notify]
        BEAT[Celery Beat]
    end
    subgraph "Data tier (stateful)"
        PGP[(PG primary)]
        PGR[(PG replicas)]
        REDIS[(Redis cluster)]
        OSC[(OpenSearch)]
        MINIO[(MinIO)]
    end
    NGINX --> A1 & W1
    A1 --> AI1
    A1 --> PGP & PGR & REDIS & OSC
    W1 --> REDIS
    C1 & C2 & C3 & C4 --> REDIS & PGP & OSC & MINIO
    AI1 --> MINIO & REDIS & PGR
```

v1 ships on **Docker Compose** (single host / small cluster). The same containers are Kubernetes-ready (manifests/Helm chart added at scale — see [DevOps](10-devops-deployment.md)).

## 2.7 Environments
`local` → `dev` → `staging` → `production`, each fully isolated (own DB, Redis namespace, buckets, secrets). Config via environment variables only (12-factor).

## 2.8 Cross-cutting concerns
- **Observability:** structured JSON logs → OpenSearch; metrics (Prometheus) → Grafana; tracing (OpenTelemetry) across API→AI→workers; Sentry for errors.
- **Idempotency:** all ingestion keyed by source-id; notifications deduped by `(rule, event, user)` hash.
- **Backpressure:** bounded queues; drop-oldest for non-critical streams, never for alerts/payments.
- **Feature flags:** central table + Redis cache, evaluated per request (see [Admin](09-admin-panel.md)).
