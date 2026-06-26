# 7. API Design

[← Back to master](../ARCHITECTURE.md)

## 7.1 Conventions
- **Base:** `https://api.finpulse.app/api/v1` · **Versioned** in path.
- **Auth:** `Authorization: Bearer <access_jwt>` unless marked *Public*.
- **Content:** `application/json`; idempotency via `Idempotency-Key` header on POST payments/orders.
- **Pagination:** cursor (`?cursor=…&limit=`) for feeds; page/size for admin tables.
- **Filtering:** `?filter[field]=…&sort=-created_at`. **Sparse fields:** `?fields=…`.
- **Errors:** standard envelope (see [backend §4.4](03-backend-structure.md)). HTTP codes: 200/201/204, 400, 401, 403, 404, 409, 422, 429, 5xx.
- **Rate limiting:** per-IP + per-user + per-API-key tiers (Redis token bucket); `429` with `Retry-After`.
- **Realtime:** REST for state, **WebSocket** for streams (see §7.14).
- **Docs:** OpenAPI 3.1 auto-generated (`drf-spectacular`) → Swagger UI at `/api/docs`, and AI service docs at `/ai/docs`.

Permission legend: 🌐 Public · 👤 Authenticated · ⭐ Plan-gated (Pro/Elite) · 🛡️ Admin/role.

---

## 7.2 `/auth` — Authentication

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/auth/register` | 🌐 | Email/password signup → sends verification |
| POST | `/auth/login` | 🌐 | Email/password → access+refresh (or 2FA challenge) |
| POST | `/auth/refresh` | 🌐(refresh) | Rotate access token |
| POST | `/auth/logout` | 👤 | Revoke current session |
| POST | `/auth/logout-all` | 👤 | Revoke all sessions |
| POST | `/auth/verify-email` | 🌐 | Confirm email with token |
| POST | `/auth/resend-verification` | 🌐 | Resend |
| POST | `/auth/forgot-password` | 🌐 | Send reset OTP/link |
| POST | `/auth/reset-password` | 🌐 | Reset with token |
| POST | `/auth/otp/request` | 🌐 | Request login/verify OTP (email/SMS) |
| POST | `/auth/otp/verify` | 🌐 | Verify OTP → tokens |
| POST | `/auth/oauth/google` | 🌐 | Exchange Google id_token |
| POST | `/auth/oauth/apple` | 🌐 | Exchange Apple identity token |
| POST | `/auth/2fa/setup` | 👤 | Begin TOTP enrolment (returns secret/QR) |
| POST | `/auth/2fa/verify` | 👤 | Confirm & enable 2FA |
| POST | `/auth/2fa/disable` | 👤 | Disable (requires password/OTP) |
| GET | `/auth/sessions` | 👤 | List active sessions/devices |
| DELETE | `/auth/sessions/{id}` | 👤 | Revoke a session |

**Example — `POST /auth/login`**
```jsonc
// request
{ "email": "a@b.com", "password": "•••", "device": { "platform": "ios", "push_token": "…" } }
// 200 (no 2FA)
{ "success": true, "data": {
  "access": "jwt…", "refresh": "jwt…", "expires_in": 900,
  "user": { "id": "…", "email": "a@b.com", "roles": ["free"] } } }
// 200 (2FA required)
{ "success": true, "data": { "challenge": "2fa", "challenge_token": "…" } }
```
Validation: email format, password ≥ 8 + complexity. Throttle: 5/min/IP, lockout after 10 fails. Permissions: public.

---

## 7.3 `/users` & `/profile`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/users/me` | 👤 | Current user + roles + entitlements |
| PATCH | `/users/me` | 👤 | Update name, phone |
| DELETE | `/users/me` | 👤 | Soft-delete account (GDPR) |
| GET | `/profile` | 👤 | Profile + preferences |
| PATCH | `/profile` | 👤 | Update avatar, country, tz, base_currency, language, risk |
| GET | `/profile/devices` | 👤 | List devices |
| DELETE | `/profile/devices/{id}` | 👤 | Remove device |
| GET | `/profile/activity` | 👤 | Login history |

---

## 7.4 `/markets` — metadata & discovery

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/markets/exchanges` | 🌐 | List exchanges |
| GET | `/markets/sectors` | 🌐 | Sector tree |
| GET | `/markets/movers` | 🌐 | Top gainers/losers/active `?market=&type=` |
| GET | `/markets/heatmap` | 🌐 | Sector/index heatmap data |
| GET | `/markets/status` | 🌐 | Open/closed sessions per exchange |

## 7.5 `/stocks`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/stocks` | 🌐 | Screener/list `?exchange=&sector=&filter[...]` |
| GET | `/stocks/{symbol}` | 🌐 | Detail (company, last quote, stats) |
| GET | `/stocks/{symbol}/quote` | 🌐 | Latest quote (Redis-cached) |
| GET | `/stocks/{symbol}/history` | 🌐 | OHLC `?interval=1d&from=&to=` |
| GET | `/stocks/{symbol}/indicators` | 🌐 | `?names=rsi,macd&interval=1d` |
| GET | `/stocks/{symbol}/news` | 🌐 | Related news |
| GET | `/stocks/{symbol}/peers` | 🌐 | Peer comparison |
| GET | `/stocks/{symbol}/forecast` | ⭐ | AI price forecast (proxy to AI svc) |
| GET | `/stocks/{symbol}/fundamentals` | 🌐 | Financials |

**Example — `GET /stocks/RELIANCE/history?interval=1d&from=2025-01-01`**
```jsonc
{ "success": true, "data": {
  "symbol": "RELIANCE", "exchange": "NSE", "interval": "1d",
  "candles": [ { "ts":"2025-01-01T00:00:00Z","o":1234.5,"h":1250,"l":1228,"c":1245,"v":3200000 } ] },
  "meta": { "count": 250 } }
```

## 7.6 `/forex`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/forex/pairs` | 🌐 | List pairs |
| GET | `/forex/{pair}` | 🌐 | Detail (e.g. EURUSD) |
| GET | `/forex/{pair}/quote` | 🌐 | Bid/ask/last |
| GET | `/forex/{pair}/history` | 🌐 | OHLC |
| GET | `/forex/{pair}/indicators` | 🌐 | TA |
| GET | `/forex/convert` | 🌐 | `?from=USD&to=INR&amount=100` |
| GET | `/forex/{pair}/forecast` | ⭐ | AI forecast |

## 7.7 `/commodities`, `/indices`, `/etfs`, `/crypto`
Same shape as `/stocks` (`list`, `{symbol}`, `/quote`, `/history`, `/indicators`, `/forecast`). `/crypto/*` behind feature flag `crypto_enabled`.

---

## 7.8 `/news`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/news` | 🌐 | Feed `?category=&symbol=&country=&cursor=` |
| GET | `/news/{id}` | 🌐 | Article + summary + sentiment + entities |
| GET | `/news/trending` | 🌐 | High-impact / most-read |
| GET | `/news/categories` | 🌐 | Category tree |
| GET | `/news/feed/personalized` | 👤 | Based on watchlist/portfolio/follows |
| POST | `/news/{id}/bookmark` | 👤 | Bookmark |
| DELETE | `/news/{id}/bookmark` | 👤 | Remove |

```jsonc
// GET /news/{id} → data
{ "id":"…","title":"RBI holds repo rate at 6.5%","summary":"…AI 2-line…",
  "sentiment": { "label":"neutral","score":0.04,"confidence":0.88 },
  "impact_score": 78, "is_breaking": true,
  "entities": [ {"type":"country","text":"India","linked_id":"…"},
                {"type":"org","text":"RBI"} ],
  "published_at":"2026-06-26T05:30:00Z","source":"…" }
```

## 7.9 `/economic-calendar`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/economic-calendar` | 🌐 | `?from=&to=&country=&importance=` |
| GET | `/economic-calendar/{id}` | 🌐 | Event detail (actual/forecast/previous) |
| POST | `/economic-calendar/{id}/subscribe` | 👤 | Alert on release |

---

## 7.10 `/watchlists`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/watchlists` | 👤 | List (with live quotes) |
| POST | `/watchlists` | 👤 | Create (limit by plan) |
| PATCH | `/watchlists/{id}` | 👤 | Rename/reorder |
| DELETE | `/watchlists/{id}` | 👤 | Delete |
| POST | `/watchlists/{id}/items` | 👤 | Add instrument |
| DELETE | `/watchlists/{id}/items/{itemId}` | 👤 | Remove |

## 7.11 `/portfolio`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/portfolio` | 👤 | All portfolios summary |
| POST | `/portfolio` | 👤 | Create portfolio |
| GET | `/portfolio/{id}` | 👤 | Holdings + live P&L |
| POST | `/portfolio/{id}/transactions` | 👤 | Add buy/sell/dividend |
| GET | `/portfolio/{id}/performance` | 👤 | Time-weighted return, allocation, risk |
| GET | `/portfolio/{id}/analysis` | ⭐ | AI risk/diversification analysis |
| DELETE | `/portfolio/{id}` | 👤 | Delete |

## 7.12 `/alerts`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/alerts/rules` | 👤 | List rules |
| POST | `/alerts/rules` | 👤 | Create (plan-limited count) |
| PATCH | `/alerts/rules/{id}` | 👤 | Update/toggle |
| DELETE | `/alerts/rules/{id}` | 👤 | Delete |
| GET | `/alerts/history` | 👤 | Fired alerts |

```jsonc
// POST /alerts/rules
{ "name":"AAPL above 250","instrument_kind":"stock","instrument_id":"…",
  "trigger_type":"price_above","condition":{"value":250},
  "channels":["push","telegram"],"priority":"high","frequency":"once","cooldown_seconds":0 }
```
Validation: condition schema per `trigger_type` (Zod/pydantic). Permission: ownership + plan alert-count limit (429/403 if exceeded).

## 7.13 `/notifications`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/notifications` | 👤 | Inbox `?unread=true&cursor=` |
| POST | `/notifications/read` | 👤 | Mark read `{ ids: [...] }` or all |
| GET | `/notifications/preferences` | 👤 | Channel matrix + quiet hours |
| PUT | `/notifications/preferences` | 👤 | Update |
| POST | `/notifications/devices/register` | 👤 | Register push token |
| POST | `/notifications/test` | 👤 | Send test push |

---

## 7.14 WebSocket API

**Endpoint:** `wss://api.finpulse.app/ws?token=<access_jwt>` (JWT validated by Channels middleware).

Message protocol (client → server):
```jsonc
{ "action": "subscribe", "channels": ["quotes.NSE.RELIANCE", "news.IN", "alerts"] }
{ "action": "unsubscribe", "channels": ["quotes.NSE.RELIANCE"] }
{ "action": "ping" }
```
Server → client:
```jsonc
{ "channel":"quotes.NSE.RELIANCE","type":"quote","data":{"c":1245.5,"chg":0.8,"ts":"…"} }
{ "channel":"news.IN","type":"news","data":{ "id":"…","title":"…","impact_score":80 } }
{ "channel":"alerts","type":"alert","data":{ "rule_id":"…","title":"AAPL above 250" } }
{ "type":"pong" }
```
- **Authorization:** users only receive `alerts`/`portfolio.*` for their own id; quote channels are public-readable but rate-limited per connection.
- **Backpressure:** server coalesces quote frames (max N/sec per symbol per client).

---

## 7.15 `/ai`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/ai/forecast/{kind}/{id}` | ⭐ | Price forecast `?horizon=7d&model=auto` |
| GET | `/ai/sentiment/{kind}/{id}` | 👤 | Aggregated sentiment for instrument |
| GET | `/ai/technical/{kind}/{id}` | 👤 | TA summary + signals |
| GET | `/ai/patterns/{kind}/{id}` | ⭐ | Detected chart patterns |
| GET | `/ai/risk/{kind}/{id}` | ⭐ | Risk score |
| GET | `/ai/historical-analog/{kind}/{id}` | ⭐ | “This looks like …” |
| GET | `/ai/recommendations` | 👤 | Personalized ideas |
| POST | `/ai/assistant/chat` | ⭐ | LLM market assistant (streaming) |

```jsonc
// GET /ai/forecast/stock/{id}?horizon=7d → data
{ "instrument":"RELIANCE","horizon":"7d","model":"forecast_transformer@2.3.0",
  "points":[ {"target_ts":"2026-07-03","mean":1290,"low":1255,"high":1325} ],
  "confidence":0.71, "disclaimer":"Not financial advice." }
```
The Django `/ai/*` endpoints are thin proxies that (a) check entitlements/rate limits, (b) call the FastAPI AI service with a signed service JWT, (c) cache results, (d) persist to `ai_predictions`.

---

## 7.16 `/subscriptions` & `/payments`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/subscriptions/plans` | 🌐 | List plans + features |
| GET | `/subscriptions/me` | 👤 | Current subscription + entitlements |
| POST | `/subscriptions/checkout` | 👤 | Create checkout session (Stripe/Razorpay) |
| POST | `/subscriptions/cancel` | 👤 | Cancel at period end |
| POST | `/payments/webhook/{provider}` | 🌐(signed) | PSP webhook (signature-verified) |
| GET | `/payments` | 👤 | Payment history |
| GET | `/payments/invoices/{id}` | 👤 | Invoice PDF |
| POST | `/payments/iap/verify` | 👤 | Verify Apple/Google receipt |

Webhooks verify provider signature; idempotent by `provider_payment_id`.

---

## 7.17 `/search`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/search` | 🌐 | Universal `?q=&types=stock,forex,news,company` |
| GET | `/search/autocomplete` | 🌐 | Typeahead (OpenSearch completion suggester) |
| GET | `/search/saved` | 👤 | Saved searches |
| POST | `/search/saved` | 👤 | Save a search |

---

## 7.18 `/admin` (🛡️ role-gated — see [Admin Panel](09-admin-panel.md))

`/admin/users`, `/admin/roles`, `/admin/permissions`, `/admin/markets`, `/admin/news`, `/admin/ai/models`, `/admin/ai/training-jobs`, `/admin/notifications/broadcast`, `/admin/subscriptions`, `/admin/payments`, `/admin/feature-flags`, `/admin/settings`, `/admin/api-keys`, `/admin/logs`, `/admin/analytics`, `/admin/audit`. Each supports list/detail/create/update/delete with permission checks per action and full audit logging.
