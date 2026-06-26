# Docker Guide — FinPulse

[← Back to README](../README.md) · [← Architecture](ARCHITECTURE.md)

How to install, run, and operate this project with Docker on **Windows 11**. This guide covers (A) one-time setup, (B) the project's container stack, (C) day-to-day commands, and (D) troubleshooting.

> **Why Docker here?** The whole architecture (PostgreSQL+TimescaleDB, Redis, OpenSearch, MinIO, Django API, FastAPI AI, Celery, Nginx) is designed to run as containers for dev/prod parity. On Windows, TimescaleDB and Redis have no good native builds — Docker is the supported path. See [13-data-sources.md](architecture/13-data-sources.md) and [10-devops-deployment.md](architecture/10-devops-deployment.md).

---

## A. One-time setup (Windows 11)

### 1. Prerequisites (already satisfied on this machine)
- **WSL2** with a Linux distro (Ubuntu) — ✅ present (`wsl --status` shows Version 2).
- **Virtualization** enabled in BIOS/UEFI (usually on by default).

### 2. Install Docker Desktop
Installed via Windows Package Manager:
```powershell
winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
```
(Accept the **UAC prompt** when it appears.) Alternatively download the installer from <https://www.docker.com/products/docker-desktop/>.

### 3. First launch
1. Reboot if the installer asks (it adds your user to the `docker-users` group and enables WSL integration).
2. Launch **Docker Desktop** from the Start menu.
3. Accept the service agreement; choose **Use WSL 2 based engine** (default).
4. Wait until the whale icon in the system tray is steady (not animating) — that means the engine is running.

### 4. Verify the install
Open a **new** terminal (so PATH refreshes) and run:
```powershell
docker --version
docker compose version
docker run --rm hello-world      # downloads a tiny image and prints a success message
```
If `hello-world` prints "Hello from Docker!", you're ready.

> ℹ️ **Licensing:** Docker Desktop is free for personal use, education, and small businesses (<250 employees AND <$10M revenue). Larger orgs need a paid subscription. The open-source **Docker Engine** (inside WSL) is always free if you prefer the CLI-only route.

---

## B. The FinPulse container stack

> The `docker-compose.yml` lands in **Phase 1**. This section documents what it will contain so the commands below make sense ahead of time.

| Service | Image | Port(s) | Purpose |
|---------|-------|---------|---------|
| `postgres` | `timescale/timescaledb:latest-pg16` | 5432 | Primary DB + time-series hypertables |
| `redis` | `redis:7-alpine` | 6379 | Cache, Celery broker, Channels layer |
| `opensearch` | `opensearchproject/opensearch:2` | 9200 | Search + logs |
| `minio` | `minio/minio` | 9000 / 9001 | Object storage (model artifacts, uploads); 9001 = console |
| `api` | built from `backend/Dockerfile` | 8000 | Django REST + Channels (ASGI) |
| `ai` | built from `ai_service/Dockerfile` | 8100 | FastAPI AI service *(added Phase 5)* |
| `worker` | built from `backend/Dockerfile` | — | Celery workers |
| `beat` | built from `backend/Dockerfile` | — | Celery scheduler |
| `nginx` | `nginx:alpine` | 80 / 443 | Reverse proxy / TLS *(prod)* |

Two compose files:
- **`docker-compose.yml`** — base definition (all environments).
- **`docker-compose.override.yml`** — dev overrides (bind-mounts for hot reload, exposed ports, debug). Compose loads both automatically in dev.

Configuration comes from **`.env`** (copied from `.env.example`). Never commit `.env`.

---

## C. Everyday commands

### Start / stop
```powershell
# from the project root: c:\Users\suraj\Documents\Suraj\APP

docker compose up -d            # start everything in the background
docker compose ps              # list running services + health
docker compose logs -f api     # follow logs for one service (Ctrl+C to stop following)
docker compose logs -f         # follow all logs
docker compose stop            # stop containers (keeps data)
docker compose down            # stop + remove containers (keeps named volumes/data)
docker compose down -v         # ⚠️ also delete volumes = WIPES the database
```

### Build / rebuild after code or dependency changes
```powershell
docker compose build api        # rebuild one image
docker compose up -d --build    # rebuild changed images and restart
docker compose build --no-cache api   # force a clean rebuild (e.g. requirements changed)
```

### Run commands inside a container
```powershell
# Django management
docker compose exec api python manage.py migrate
docker compose exec api python manage.py makemigrations
docker compose exec api python manage.py createsuperuser
docker compose exec api python manage.py shell

# Tests / lint
docker compose exec api pytest
docker compose exec api ruff check .

# Open a shell in a container
docker compose exec api bash
docker compose exec postgres psql -U finpulse -d finpulse
```

> `exec` runs in an **already-running** container. Use `run --rm` for a one-off in a fresh container:
> ```powershell
> docker compose run --rm api python manage.py check
> ```

### Inspect & debug
```powershell
docker compose ps                       # status + ports
docker stats                            # live CPU/memory per container
docker compose exec api env             # see env vars inside a container
docker volume ls                        # list data volumes
docker network ls                       # list networks
```

### Service URLs (dev)
- API docs (Swagger): <http://localhost:8000/api/docs>
- Health check: <http://localhost:8000/healthz>
- MinIO console: <http://localhost:9001> (user/pass from `.env`)
- OpenSearch: <http://localhost:9200>

### The frontend (Expo) runs on the host, not in Docker
The mobile/web app talks to the Dockerized API over `http://localhost:8000`:
```powershell
pnpm install
pnpm --filter mobile expo start        # press w (web), i (iOS), a (Android)
```
Set `EXPO_PUBLIC_API_URL=http://localhost:8000` in the app env.

---

## D. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `docker: command not found` after install | Open a **new** terminal; ensure Docker Desktop is **running** (tray whale steady). |
| `error during connect ... dockerDesktopLinuxEngine` | Docker Desktop engine isn't started yet — launch the app and wait for it to finish booting. |
| `port is already allocated` (e.g. 5432) | Another Postgres/Redis is using the port. Stop it, or change the host port mapping in `docker-compose.override.yml`. |
| WSL2 errors / "virtual machine platform" | Run `wsl --update`, ensure "Virtual Machine Platform" + "WSL" Windows features are enabled, reboot. |
| Containers slow / high disk | Docker Desktop → Settings → Resources: raise CPU/RAM; run `docker system prune` to reclaim space. |
| DB changes not showing | You may have an old volume. `docker compose down -v` then `up` to recreate (⚠️ wipes data). |
| Permission denied on bind mount | Ensure the project folder is shared in Docker Desktop → Settings → Resources → File Sharing. |
| Image pulls fail behind proxy | Configure proxy in Docker Desktop → Settings → Resources → Proxies. |

### Useful cleanup
```powershell
docker system df                 # show disk usage
docker system prune              # remove stopped containers, unused networks, dangling images
docker system prune -a --volumes # ⚠️ aggressive: removes ALL unused images + volumes
```

---

## E. Quick reference card

```text
START:    docker compose up -d
STATUS:   docker compose ps
LOGS:     docker compose logs -f <service>
MIGRATE:  docker compose exec api python manage.py migrate
SHELL:    docker compose exec api bash
TESTS:    docker compose exec api pytest
STOP:     docker compose down          (keep data)
RESET:    docker compose down -v        (WIPE data)
REBUILD:  docker compose up -d --build
```

> This guide will be linked from the root `README.md` quickstart once Phase 1 lands the compose files.
