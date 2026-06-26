# Data Engines — Market Data · News · Charts · Search

[← Back to master](../ARCHITECTURE.md)

This file covers the four real-time/data subsystems referenced throughout: **Market Data**, **News Engine**, **Charts**, and **Search Engine**.

---

## A. Market Data Engine

### A.1 Capabilities
Live Forex · Live Stocks (NSE/BSE/US/EU) · Live Commodities · Live Indices · Live currency rates · Historical data · Real-time price updates · WebSocket streaming · OHLC/candlestick · Market movers · Heatmaps · Sector performance.

### A.2 Ingestion architecture
```mermaid
graph LR
    subgraph Providers
        WSV[Vendor WebSocket feeds]
        RSTV[Vendor REST endpoints]
    end
    WSV --> ADP[Adapter / normalizer<br/>integrations/market_data]
    RSTV --> POLL[Pollers<br/>Celery beat, tiered cadence] --> ADP
    ADP --> MAP[Symbol mapping<br/>symbol_aliases]
    MAP --> NORM[Normalize<br/>currency, tz, OHLC]
    NORM --> RC[Redis: latest:{symbol} + XADD ticks]
    NORM --> TS[(TimescaleDB batched insert)]
    RC --> PUB[Redis pub/sub] --> WSGW[Channels gateway] --> CL[Clients]
    NORM --> AGG[Continuous aggregates 1m→5m→1h→1d]
```

### A.3 Design decisions
- **Tiered polling:** liquid/popular symbols polled fast (1–5s), long-tail slower (15–60s); WebSocket vendor feeds preferred where available. User-subscribed symbols get priority.
- **Anti-corruption layer:** every vendor wrapped in `integrations/market_data/*` implementing a common interface (`get_quote`, `get_ohlc`, `stream`) with retry, circuit breaker, rate-limit, and caching. Vendor symbol → internal instrument via `symbol_aliases`.
- **Failover:** `data_provider_status` tracks health/quota; on degradation, route to backup provider automatically.
- **Latest quote** = Redis O(1); **history** = TimescaleDB hypertables; **rollups** = continuous aggregates (cheap multi-interval candles).
- **Batched writes** protect Postgres (windowed inserts). Ticks retained short-term; 1m+ retained long-term (compression on old chunks).
- **Market movers / heatmaps / sector performance** computed by periodic Celery jobs into Redis (precomputed, served instantly).

### A.4 Real-time delivery
Clients subscribe to `quotes.{exchange}.{symbol}` channels; gateway pushes only subscribed symbols; quote frames coalesced per client to cap bandwidth. NSE/BSE/US/EU sessions tracked so UI shows live vs delayed/closed correctly.

---

## B. News Engine

### B.1 Pipeline
```
News APIs / RSS / scrapers
        ↓  (poll, short interval)
Deduplicate  (URL canonicalization + sha256 + simhash near-dup)
        ↓
Categorize   (topic classifier)
        ↓
Summarize    (abstractive, length-bounded)
        ↓
Sentiment    (FinBERT → label/score/confidence)
        ↓
Impact score (source authority × entity importance × market hours × novelty)
        ↓
Entity extraction (NER → companies/tickers/currencies/people/orgs) → entity linking
        ↓
Store (Postgres news/news_sentiment/news_entities) + Index (OpenSearch)
        ↓
Notify (entity match → user watchlists/rules → priority push)
```

### B.2 Components
- **Sources:** multiple providers + RSS + (compliant) scrapers; each wrapped in `integrations/news/*`.
- **Dedup:** canonical URL hash for exact, **simhash** for near-duplicates across sources; first-seen wins, others linked as alternates.
- **NLP (AI service):** FinBERT (sentiment), sentence-transformers (embeddings for dedup/similarity/clustering), NER + entity linking, topic classification, keyword extraction, abstractive summarization. (Model details in [AI architecture §8.7](06-ai-architecture.md).)
- **Impact scoring:** ranks articles for "fastest notification" — high-impact breaking items skip batching and go to the critical/high notification queue.
- **Storage & search:** persisted + indexed in OpenSearch for full-text/filtered retrieval; personalized feed = entities ∩ user watchlist/portfolio/follows.

### B.3 Speed target
Source publish → user notification **p95 < 5s**: short poll interval + parallel NLP workers + impact-based fast-path that bypasses non-critical batching.

---

## C. Charts

### C.1 Chart types
Candlestick · OHLC · Area · Line · Bar · Volume · Heatmap · Treemap · Correlation matrix.

### C.2 Technical indicators
RSI · MACD · EMA · SMA · VWAP · ATR · ADX · Ichimoku · Bollinger Bands · Fibonacci.

### C.3 Compute & delivery
- Indicators computed **server-side** (consistent, heavy math off-device) in `ai_service`/backend indicator engine, cached in Redis + persisted (`technical_indicators`) for popular symbols; delivered as overlays via `/…/indicators`.
- Lightweight client copy in `utils/math` for instant preview while server data loads.
- **Rendering:** Victory Native + react-native-svg; high-interaction charts use Reanimated + Skia for 60fps pan/zoom (mobile), Victory on web.
- **Saved charts:** interval, indicator set, and drawings persisted via `saved_charts` and restored across devices; optional public sharing with snapshot to MinIO.
- **Data source:** candles from `/…/history` (TimescaleDB rollups); live last-candle updated via WebSocket quote stream.

---

## D. Search Engine (OpenSearch)

### D.1 Capabilities
Company search · Ticker/symbol search · News search · Forex pair search · Commodity search · Sector search · Country search · Autocomplete · Filters.

### D.2 Index design
| Index | Key fields | Features |
|-------|-----------|----------|
| `instruments` | symbol, name, exchange, asset_class, sector, aliases | completion suggester (autocomplete), boosting by popularity/liquidity, fuzzy |
| `companies` | name, sector, country, isin, description | full-text + filters |
| `news` | title, body, summary, entities, category, published_at, sentiment, impact | full-text, time + facet filters, kNN (embedding) for "similar news" |
| `economic_events` | name, country, importance, time | filtered search |

### D.3 Architecture
```mermaid
graph LR
    PG[(Postgres)] -->|signals/Celery indexers| IDX[Indexers<br/>search/documents]
    IDX --> OS[(OpenSearch cluster)]
    API[/search, /search/autocomplete] --> OS
    NLP[News embeddings] --> OS
```
- **Indexing:** on write (Django signals → Celery indexer) + periodic reconcile/reindex jobs; bulk indexing for backfills.
- **Autocomplete:** completion suggester + edge-ngram for instant typeahead; personalization via `search_history`.
- **Universal search:** multi-index query with per-type boosting; results grouped by type (stock/forex/news/company).
- **Relevance:** boost by liquidity/popularity, recency for news; fuzzy for typos; synonyms (e.g. "Apple"↔AAPL).
- **kNN semantic** search for "find similar news/analyses" using sentence-transformer embeddings stored in OpenSearch.
- Also doubles as the **log/analytics** store (structured logs, `analytics_events`).
