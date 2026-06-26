# Free Data Sources (and where paid is needed)

[← Back to master](../ARCHITECTURE.md)

> ⚠️ **Verify before coding.** Free-tier limits, terms, and even availability change frequently, and **redistribution/commercial terms vary** (many free feeds forbid public redistribution — critical for a multi-user product). Treat the numbers below as *approximate, last known* and confirm each provider's current pricing + license before integrating. The architecture's anti-corruption layer ([data-engines §A.3](12-data-engines.md)) makes swapping providers cheap.

## Stocks (US / global)

| Provider | Free tier (approx) | Strengths | Limitations |
|----------|-------------------|-----------|-------------|
| **Alpha Vantage** | ~25 req/day, 5/min | Easy, broad (stocks/FX/crypto, some fundamentals/indicators) | Very low limits; delayed; not for realtime/redistribution |
| **Twelve Data** | ~800 req/day, 8/min | Stocks/FX/crypto, WebSocket on paid | Free is delayed & capped; realtime needs paid |
| **Finnhub** | generous free REST + some WS | Realtime-ish US quotes, news, fundamentals | Non-US realtime + heavy use need paid; redistribution limited |
| **Financial Modeling Prep** | limited free | Deep fundamentals/financial statements | Tight free caps; paid for full history |
| **yfinance (Yahoo, unofficial)** | "free" (scraping) | Huge coverage, history, fundamentals | **Unofficial, no SLA/ToS for commercial use** — dev/prototyping only, not production |
| **Tiingo** | limited free | EOD + some intraday, news | Caps; paid for realtime |

## Indian market (NSE / BSE)

| Provider | Notes |
|----------|-------|
| **NSE/BSE public endpoints** | Unofficial JSON endpoints exist but are **rate-limited, unstable, and not licensed for redistribution** — fragile for production. |
| **Broker APIs** (Zerodha Kite, Upstox, Angel One, Dhan, Fyers) | Reliable realtime + historical for **authenticated account holders**; often per-user, not a public data license. Good for personal/portfolio features; check market-data redistribution terms. |
| **Twelve Data / Alpha Vantage** | Some NSE/BSE coverage, delayed on free tiers. |
| **Production reality** | Real NSE/BSE realtime + redistribution requires a **licensed exchange data vendor** (paid, exchange-approved). Budget for this. |

## Forex / currency

| Provider | Free tier | Limitations |
|----------|-----------|-------------|
| **exchangerate.host / Frankfurter (ECB)** | free reference rates | Daily/EOD reference, not tick-level tradable quotes |
| **Alpha Vantage / Twelve Data FX** | capped, delayed | No realtime tick stream on free |
| **OANDA / Polygon.io** | limited free / paid | Realtime FX, proper streaming → paid |

## News

| Provider | Free tier | Limitations |
|----------|-----------|-------------|
| **NewsAPI.org** | dev free (limited, **non-commercial**) | Not for production/commercial; delayed; limited sources |
| **GNews** | small free tier | Low limits |
| **Marketaux** | free tier with finance focus + entities/sentiment | Caps on requests & history |
| **RSS feeds** (Reuters/Moneycontrol/ET/Investing/exchange filings) | free | Parsing varies, no sentiment, must dedup & enrich yourself (our pipeline does this) |
| **Finnhub news** | free company/market news | Coverage/limits |

## Economic calendar / macro

| Provider | Free tier | Limitations |
|----------|-----------|-------------|
| **FRED (St. Louis Fed)** | free, generous | US macro series (excellent), not a global "calendar" of releases |
| **Trading Economics** | limited free / paid | Best global calendar; full access is paid |
| **Investing.com calendar** | scrape (no official free API) | ToS-sensitive; fragile |
| **World Bank / IMF / OECD** | free | Low-frequency macro, not realtime releases |

## Historical data
Alpha Vantage / Twelve Data / Tiingo / yfinance / Stooq (free EOD) for backfill and model training. Free history is often limited in depth/resolution; deep intraday history is typically paid. Use free for prototyping/training, then backfill from a paid vendor for production depth.

## Sentiment / NLP data
We **generate** sentiment in-house (FinBERT + transformers) from news text — no paid sentiment feed required. Optional enrichment: Marketaux/Finnhub include basic sentiment; social sentiment (e.g. StockTwits/X) is largely paid or ToS-restricted.

## LLM assistant
**Anthropic Claude API** (paid, usage-based) powers the assistant + summaries grounding. Use the latest capable model; check the `/claude-api` reference for current model IDs and pricing before integrating. HuggingFace open models (FinBERT etc.) are self-hosted in the AI service (free to run, you pay compute).

---

## Recommended path
1. **Prototype / dev:** Alpha Vantage + Twelve Data + Finnhub + FRED + RSS/Marketaux + yfinance (non-prod) — enough to build every feature.
2. **Production (where paid is unavoidable):**
   - **Realtime quotes & streaming** (esp. NSE/BSE, FX ticks): licensed paid vendor — required for the "fastest" promise and for legal redistribution to many users.
   - **Deep intraday history:** paid backfill.
   - **Global economic calendar:** Trading Economics paid.
   - **News at scale + commercial license:** paid news API (NewsAPI commercial / Marketaux paid / dedicated wire).
   - **LLM:** Anthropic Claude (paid).
3. Keep everything behind the **provider abstraction** so free→paid is a config swap with health/quota-based failover (`data_provider_status`).
