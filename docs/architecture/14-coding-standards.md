# Coding Standards & Documentation

[← Back to master](../ARCHITECTURE.md)

## Architecture principles (apply everywhere)
- **Clean / layered architecture:** views/controllers → services → repositories → models. Dependencies point inward.
- **Feature-based modularity:** vertical slices (frontend `features/*`, backend `apps/*`). A feature owns its UI, logic, data access, types.
- **SOLID:** single-responsibility services, interface-segregated integrations, dependency inversion (depend on abstractions/protocols).
- **Repository pattern:** all ORM access behind repositories; services never see raw `.objects` elsewhere.
- **Service layer:** business logic + transactions live in services, not views/serializers.
- **Dependency injection** where it adds value (provider clients, model registry, cache) — constructor/factory injection so tests can substitute fakes.
- **Anti-corruption layer:** external APIs wrapped; internal code never depends on a vendor's shape.

## Python / Django / FastAPI
- **PEP 8**, formatted by **black**, linted by **ruff**; imports sorted (ruff/isort).
- **Type hints everywhere**; **mypy** in CI (strict on services/repositories). Pydantic for FastAPI I/O.
- Docstrings (Google style) on public services/functions. No business logic in serializers or views.
- Settings via env only; no secrets/constants hardcoded. Use `select_related/prefetch_related` to avoid N+1.
- Celery tasks: idempotent, small, retry-safe, with explicit queues and time limits.
- Tests colocated per app (`apps/<x>/tests/`), factory_boy fixtures, no live network in unit tests.

## TypeScript / React Native
- **Strict TypeScript** (`strict: true`, no `any`, no implicit any, `noUncheckedIndexedAccess`).
- **ESLint + Prettier**; import order enforced; absolute imports via path aliases.
- **Reusable components** in `packages/ui` / `components/common`; feature components stay in their slice.
- **State policy** (see [frontend §3.4](02-frontend-structure.md)): React Query = server state, Zustand = client state, RHF+Zod = forms. Never duplicate server data into Zustand.
- Functional components + hooks only; side effects in hooks/services, not in render.
- Shared validation schemas (Zod) reused between forms and API parsing; shared domain types mirror backend (`packages/types`).
- Accessibility: labels, roles, hit slop, color-contrast tokens; i18n keys (no hardcoded strings).

## API & data conventions
- REST: plural nouns, versioned (`/api/v1`), standard response envelope, consistent error codes.
- Time: store/transmit **UTC ISO-8601**; convert at the edge using user timezone.
- Money: integers/`Decimal`/`NUMERIC(20,8)`, never float; always carry currency.
- Naming: `snake_case` (Python/DB), `camelCase` (TS), `PascalCase` (components/classes), `SCREAMING_SNAKE` (constants).
- DB: every table has UUID PK, `created_at`, `updated_at`, soft delete where applicable; every FK indexed.

## Git & process
- Conventional Commits (`feat:`, `fix:`, `chore:`…); trunk-based with short-lived feature branches.
- PRs require: green CI, review, no decrease in coverage, updated docs for API/schema changes.
- Pre-commit hooks: format, lint, type-check, secret scan.

## Documentation deliverables
| Doc | Location | Content |
|-----|----------|---------|
| **README** | `/README.md` | Overview, quickstart, env setup, run with Docker, scripts |
| **API docs** | OpenAPI (`/api/docs`) + `docs/api/` | Auto-generated + curated guides, auth, examples |
| **Architecture docs** | `docs/architecture/` (this set) | The master blueprint |
| **Database docs** | `docs/architecture/04-database-schema.md` | Schema, ER, partitioning, retention |
| **Deployment guide** | `docs/deployment.md` | Envs, CI/CD, scaling, backups/DR, runbooks |
| **Developer guide** | `docs/developer-guide.md` | Local setup, conventions, how to add a feature/app |
| **Coding standards** | this file | The rules above |
| **Contribution guide** | `CONTRIBUTING.md` | Branching, PR flow, commit style, review checklist |
| **Changelog** | `CHANGELOG.md` | Keep-a-Changelog format |

## Definition of Done (per feature)
Implemented across layers · typed · validated · tested (unit+integration, ≥ coverage) · documented (API + dev guide) · observable (logs/metrics) · secured (authz + input validation) · accessible + i18n · behind a feature flag if risky.
