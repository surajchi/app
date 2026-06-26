# 3. Frontend Folder Structure

[← Back to master](../ARCHITECTURE.md)

**Stack:** React Native · Expo (SDK, EAS Build) · React Native Web · TypeScript (strict) · Zustand (client state) · React Query / TanStack Query (server state) · React Navigation · React Hook Form + Zod · NativeWind (Tailwind) · Reanimated · Victory Native (charts) · react-native-svg.

**Architecture:** Feature-based (vertical slices) + a shared core. One codebase → iOS, Android, Web.

## 3.1 Monorepo top level

```
finpulse/
├── apps/
│   ├── mobile/                  # Expo app (iOS, Android, Web via RN Web)
│   └── admin/                   # Admin dashboard (can be RN Web or Next.js; see §12)
├── packages/
│   ├── ui/                      # Shared design-system components
│   ├── api-client/              # Generated/typed API SDK (OpenAPI → TS)
│   ├── types/                   # Shared domain types (mirror backend)
│   └── config/                  # Shared eslint/tsconfig/tailwind presets
├── backend/                     # Django + FastAPI (see backend doc)
├── docs/
├── docker-compose.yml
└── package.json                 # workspaces (pnpm/yarn)
```

## 3.2 `apps/mobile/src` — full tree

```
src/
├── app/                         # App entry, root providers, deep-link config, error boundary
│   ├── App.tsx
│   ├── RootProvider.tsx         # composes all providers (Query, Theme, Auth, i18n…)
│   └── bootstrap.ts             # env load, sentry init, font load, splash
│
├── navigation/                  # React Navigation tree
│   ├── RootNavigator.tsx        # switches Auth vs App stacks
│   ├── AuthNavigator.tsx
│   ├── AppNavigator.tsx         # bottom tabs + nested stacks
│   ├── linking.ts               # deep links / universal links
│   └── types.ts                 # typed route params
│
├── components/                  # SHARED, feature-agnostic UI only
│   ├── common/
│   │   ├── buttons/             # Button, IconButton, FAB
│   │   ├── cards/               # Card, StatCard, AssetCard
│   │   ├── charts/              # Chart primitives wrapping Victory/SVG
│   │   ├── modals/              # BottomSheet, ConfirmModal, ActionSheet
│   │   ├── forms/               # Input, Select, Toggle, DatePicker (RHF-bound)
│   │   ├── feedback/            # Toast, Skeleton, EmptyState, ErrorState
│   │   └── data/                # Table, List, Badge, Pill, Sparkline
│   └── layouts/                 # Screen, Section, SafeArea, Header, TabBar
│
├── features/                    # ★ vertical slices — the heart of the app
│   ├── authentication/
│   ├── dashboard/
│   ├── markets/
│   │   ├── forex/
│   │   ├── stocks/
│   │   ├── commodities/
│   │   ├── indices/
│   │   ├── etfs/
│   │   └── crypto/
│   ├── portfolio/
│   ├── watchlists/
│   ├── alerts/
│   ├── news/
│   ├── ai/                      # AI insights, forecasts, chat assistant
│   ├── economic_calendar/
│   ├── search/
│   ├── profile/
│   ├── settings/
│   ├── subscriptions/
│   ├── payments/
│   └── admin/                   # lightweight admin entry (full admin = apps/admin)
│
├── hooks/                       # cross-feature reusable hooks
│   ├── useDebounce.ts
│   ├── useWebSocket.ts          # generic socket subscription
│   ├── useColorScheme.ts
│   ├── useNetworkStatus.ts
│   └── useAppState.ts
│
├── store/                       # Zustand stores (CLIENT state only)
│   ├── authStore.ts             # tokens, user, session
│   ├── uiStore.ts               # theme, drawer, modals
│   ├── watchlistStore.ts        # optimistic local mirror
│   ├── preferencesStore.ts      # language, currency, notif prefs
│   └── index.ts
│
├── services/                    # I/O boundary (no UI)
│   ├── api/
│   │   ├── client.ts            # axios/fetch instance, interceptors, retry
│   │   ├── endpoints.ts         # path constants
│   │   ├── queryKeys.ts         # TanStack Query key factory
│   │   └── resources/           # one file per domain (auth, stocks, news…)
│   ├── websocket/
│   │   ├── socketManager.ts     # connect, reconnect, heartbeat, multiplex
│   │   ├── channels.ts          # channel name builders
│   │   └── handlers.ts
│   ├── notifications/
│   │   ├── push.ts              # Expo notifications / FCM / APNs token
│   │   ├── handlers.ts          # foreground/background handlers
│   │   └── categories.ts
│   ├── payments/
│   │   ├── stripe.ts            # / razorpay.ts (India)
│   │   └── iap.ts               # Apple/Google in-app purchase
│   ├── authentication/
│   │   ├── oauthGoogle.ts
│   │   ├── oauthApple.ts
│   │   ├── otp.ts
│   │   └── secureStore.ts       # token storage (Keychain/Keystore)
│   └── storage/                 # MMKV / AsyncStorage wrappers
│
├── providers/                   # React context providers
│   ├── QueryProvider.tsx
│   ├── ThemeProvider.tsx
│   ├── AuthProvider.tsx
│   ├── I18nProvider.tsx
│   ├── ToastProvider.tsx
│   └── WebSocketProvider.tsx
│
├── contexts/                    # lightweight contexts (non-provider helpers)
│
├── theme/                       # design tokens
│   ├── tokens.ts                # colors, spacing, radii, typography scale
│   ├── light.ts / dark.ts
│   ├── tailwind.config.js       # NativeWind theme
│   └── index.ts
│
├── constants/                   # app-wide constants & enums
│   ├── config.ts                # API base URLs, feature toggles
│   ├── markets.ts               # exchange codes, sessions, currencies
│   ├── intervals.ts             # 1m/5m/1h/1d chart intervals
│   └── routes.ts
│
├── types/                       # global TS types (domain mirrors backend)
│   ├── models.ts                # Stock, ForexPair, NewsItem, Portfolio…
│   ├── api.ts                   # request/response DTOs
│   └── navigation.ts
│
├── utils/                       # pure helpers (no side effects)
│   ├── format/                  # number, currency, percent, date, abbreviations
│   ├── math/                    # indicators (RSI/MACD/EMA helpers for client preview)
│   ├── validation/              # zod schemas shared with RHF
│   └── color/                   # gain/loss coloring, heatmap scales
│
├── config/                      # env-driven runtime config
│   ├── env.ts                   # typed env (expo-constants)
│   └── flags.ts                 # client-side feature flag reader
│
├── locales/                     # i18n (i18next)
│   ├── en/  hi/  es/  ar/ …     # per-language JSON namespaces
│   └── index.ts
│
└── assets/
    ├── fonts/
    ├── images/
    ├── icons/
    └── animations/              # Lottie / Reanimated assets
```

## 3.3 Anatomy of a feature slice (mandatory shape)

Every folder under `features/` follows the **same** structure so it's predictable for humans and AI agents:

```
features/<feature>/
├── components/      # UI specific to this feature
├── screens/         # navigable screens (registered in navigation)
├── hooks/           # feature hooks (often wrap React Query + services)
├── services/        # feature API calls (thin wrappers over services/api)
├── store/           # (optional) feature-local Zustand slice
├── types/           # feature DTOs & view models
├── utils/           # feature-pure helpers
├── constants/       # feature constants
└── index.ts         # public surface (only export what other features may use)
```

### Example: `features/markets/stocks/`
```
stocks/
├── components/
│   ├── StockHeader.tsx          # price, change, day range
│   ├── StockChart.tsx           # candlestick + indicators
│   ├── IndicatorPanel.tsx
│   ├── OrderBookLite.tsx
│   ├── FundamentalsTable.tsx
│   └── PeerComparison.tsx
├── screens/
│   ├── StockListScreen.tsx      # screener / movers
│   ├── StockDetailScreen.tsx
│   └── StockScreenerScreen.tsx
├── hooks/
│   ├── useStockQuote.ts         # React Query + WS live override
│   ├── useStockHistory.ts       # OHLC by interval
│   ├── useStockNews.ts
│   └── useStockForecast.ts      # AI service
├── services/stocksApi.ts
├── types/stock.ts
├── utils/stockFormat.ts
├── constants/exchanges.ts
└── index.ts
```

## 3.4 State management policy (critical)

| Kind of state | Tool | Rule |
|---------------|------|------|
| **Server data** (quotes, news, lists) | **React Query** | Source of truth, cached, invalidated; never duplicated into Zustand |
| **Live overrides** (WS ticks) | React Query `setQueryData` patch from WS | WS updates the same cache key the REST read populated |
| **Client/UI state** (theme, drawer, auth tokens, prefs) | **Zustand** | Small, persisted slices |
| **Form state** | **React Hook Form + Zod** | Validation schemas shared from `utils/validation` |

This avoids the #1 RN bug class: two copies of the same data drifting.

## 3.5 Charts strategy
- **Victory Native + react-native-svg** for candlestick, OHLC, line, area, bar, volume.
- Heavy/interactive charts use **Reanimated + Skia path** rendering for 60fps pan/zoom on mobile; Victory on web.
- Indicator math (RSI/MACD/EMA/Bollinger/Fibonacci) computed server-side and delivered as overlays; a lightweight client copy in `utils/math` enables instant previews.
- Chart config (interval, indicators, drawings) persisted via `saved_charts` API.

## 3.6 Performance & UX
- **FlashList** (not FlatList) for large symbol/news lists.
- **MMKV** for synchronous storage (faster than AsyncStorage).
- Suspense + skeleton states everywhere; optimistic updates for watchlist/alert toggles.
- Reanimated layout animations; haptics on key actions.
- **Dark mode** via theme tokens; **multi-language + RTL** via i18next.
- Offline-first: React Query persistence + queued mutations replay on reconnect.

## 3.7 Admin dashboard (`apps/admin`)
Recommended as a **separate Next.js (React) web app** (data-dense tables, server components, easier SSR/SEO-irrelevant but better DX for grids) sharing `packages/ui`, `packages/types`, and `packages/api-client`. If team prefers one toolchain, it can be RN Web — but Next.js is the recommendation for the admin grid/dashboard workload. See [Admin Panel](09-admin-panel.md).
