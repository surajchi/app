# 12. Admin Panel

[← Back to master](../ARCHITECTURE.md)

A dedicated operational control plane (separate web app `apps/admin`, recommended Next.js — see [frontend §3.7](02-frontend-structure.md)), backed by the `/api/v1/admin/*` API and `apps/admin_panel` Django app. Every action is RBAC-gated and **audited**.

## 12.1 Modules

| Module | Capabilities |
|--------|--------------|
| **Dashboard** | KPIs: DAU/MAU, new signups, active subs, MRR/ARR, churn, notifications sent, ingestion health, AI model accuracy, infra status. |
| **Users** | Search/filter, view profile + activity + sessions/devices, suspend/restore, soft-delete, impersonate (super_admin, audited), reset 2FA, adjust plan. |
| **Roles** | Create/edit roles, assign permission sets, view users per role. |
| **Permissions** | Manage permission codes; map to roles (no code deploy needed). |
| **Market Management** | CRUD exchanges, symbols/instruments, symbol aliases (vendor mapping), enable/disable instruments, trigger backfills, manage corporate actions/market events. |
| **News Management** | Moderate/approve/reject articles, edit summaries, manage categories, manage sources, re-run NLP, flag/blacklist sources, push breaking-news broadcast. |
| **AI Model Management** | View `ml_models`/`model_versions`, metrics & drift, trigger `training_jobs`, promote staging→production / rollback, view prediction accuracy dashboards. |
| **Notification Management** | Compose/schedule broadcasts (segment by plan/role/region/watchlist), templates, delivery analytics (sent/delivered/failed/opened), retry failed. |
| **Subscriptions** | Manage plans (price/features/limits), view/modify user subscriptions, grant comps/trials, handle dunning. |
| **Payments** | Transactions, invoices, refunds (via PSP), reconcile webhooks, revenue reports. |
| **Feature Flags** | Toggle features, % rollout, target by plan/role/region; instant (Redis-cached). |
| **System Settings** | Global config (`system_settings`), provider keys status, maintenance mode, rate-limit tiers. |
| **API Keys** | Issue/scope/rotate/revoke keys (internal & partner), view usage & quotas. |
| **Logs** | Application logs (from OpenSearch), error explorer (Sentry link), data-provider status & quota. |
| **Analytics** | Product analytics (funnels, retention, feature usage), market data usage, AI usage per plan. |
| **Audit Trail** | Searchable `audit_logs` (actor, action, resource, before/after, IP, time); export. |

## 12.2 Admin API surface (recap)
`/admin/users`, `/admin/roles`, `/admin/permissions`, `/admin/markets/*`, `/admin/news/*`, `/admin/ai/models`, `/admin/ai/training-jobs`, `/admin/notifications/broadcast`, `/admin/subscriptions`, `/admin/payments`, `/admin/feature-flags`, `/admin/settings`, `/admin/api-keys`, `/admin/logs`, `/admin/analytics`, `/admin/audit`.

Each: list (filter/sort/paginate) · detail · create · update · delete — with per-action permission codes and audit logging.

## 12.3 Access control
- Only `super_admin`, `admin`, `moderator` roles reach `/admin/*`. Each module action maps to a permission code (e.g. `ai.train`, `payments.refund`, `user.impersonate`). Moderators get a restricted subset (news moderation, flag handling).
- **Impersonation** issues a scoped, time-boxed token, banner-visible in app, fully audited, super_admin-only.

## 12.4 Two layers of admin
1. **Custom Admin Panel** (`apps/admin` + `/admin/*` API) — the product-grade operational UI above.
2. **Django Admin** (`/django-admin/`) — restricted to super_admin over VPN/IP-allowlist for low-level data fixes and emergencies; not the primary tool.

## 12.5 Operational dashboards (embedded)
Grafana panels (infra, ingestion lag, queue depth, AI accuracy/drift, error rates) embedded in the admin dashboard for one-pane operations.
