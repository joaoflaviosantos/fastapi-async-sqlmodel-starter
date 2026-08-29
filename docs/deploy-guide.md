# Deployment Guide

This guide describes all available deployment modes for the project. Choose the one that best fits your infrastructure.

For local development setup, see the [Development Guide](development-guide.md). The root `python setup.py` CLI is for local run and project tools (tests, Alembic, Locust); it does not deploy.

---

## Overview

```
deploy/
├── compose/
│   ├── full-stack/     → Complete stack on a single VPS (Docker + Caddy HTTPS)
│   └── app-only/       → Application only (external databases, PaaS platforms)
└── native/             → Linux VPS without Docker (Nginx + Supervisor)
```

| Mode                                      | Best For                 | Docker | HTTPS             | DB Included |
| ----------------------------------------- | ------------------------ | ------ | ----------------- | ----------- |
| [compose/full-stack](#-composefull-stack) | Single VPS, full control | ✅     | ✅ Caddy          | ✅          |
| [compose/app-only](#-composeapp-only)     | PaaS, managed databases  | ✅     | ❌ (platform)     | ❌          |
| [native](#-native)                        | Linux VPS, no Docker     | ❌     | ❌ Nginx (manual) | ❌          |

---

## 🐳 compose/full-stack

> Full documentation: [deploy/compose/full-stack/README.md](../deploy/compose/full-stack/README.md)

**When to use:** You want to run the entire stack (databases, API, workers, reverse proxy, TLS) on a **single VPS** with a single `docker compose up` command.

**What's included:**

| Service         | Description                                         |
| --------------- | --------------------------------------------------- |
| `caddy`         | Reverse proxy with automatic Let's Encrypt HTTPS    |
| `postgres`      | PostgreSQL 17 with pgvector (internal network only) |
| `redis`         | Redis Alpine (internal network only)                |
| `migrate`       | Runs `alembic upgrade head` once before API starts  |
| `api`           | FastAPI via Uvicorn                                 |
| `celery_worker` | Celery Worker                                       |
| `celery_beat`   | Celery Beat scheduler                               |
| `celery_flower` | Flower UI (basic auth required, internal)           |

**Key features:**

- PostgreSQL and Redis are **not** exposed to the host (no port binding).
- Healthchecks on Postgres and Redis prevent the API from starting before the databases are ready. The `api` container probes `GET /health` (liveness). `GET /ready` checks Postgres and Redis before the instance should receive traffic.
- Caddy automatically provisions TLS certificates. Edit `deploy/compose/full-stack/Caddyfile` with your domain to enable HTTPS.
- The `api` service sets `TRUST_PROXY_HEADERS=True` so anonymous rate limits use the client IP Caddy forwards, not Caddy's own address. Details: [Rate Limit Guide](rate-limit-guide.md).

**Prerequisites:**

1. Docker and Docker Compose on the server.
2. `backend/.env` configured from `backend/.env.example`.
3. Ports `80` and `443` open in the firewall.
4. DNS A record pointing to the server's IP.

**Run (from repository root):**

Start main stack (Postgres, Redis, API, Caddy):

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod up -d
```

Run migration:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile migrate run --rm migrate
```

Start Celery Worker:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile worker up -d celery_worker
```

Start Celery Beat:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile scheduler up -d celery_beat
```

Start Flower (Observability):

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile observability up -d celery_flower
```

---

## 🐳 compose/app-only

> Full documentation: [deploy/compose/app-only/README.md](../deploy/compose/app-only/README.md)

**When to use:** Your databases are **managed externally** — by a PaaS platform or a cloud service — and you only want to deploy the application containers.

**Compatible with:**

- Self-managed: Dokploy, Coolify, CapRover, Portainer
- Cloud: AWS ECS, Railway, Render, Fly.io
- Managed databases: AWS RDS + ElastiCache, Supabase, Neon, Upstash

**What's included:**

| Service         | Description                                  |
| --------------- | -------------------------------------------- |
| `migrate`       | Runs `alembic upgrade head` once, then exits |
| `api`           | FastAPI via Uvicorn                          |
| `celery_worker` | Celery Worker                                |
| `celery_beat`   | Celery Beat scheduler                        |
| `celery_flower` | Flower UI (basic auth required)              |

**Key features:**

- No Postgres, Redis, or reverse proxy containers.
- Uses an external Docker network (`app-network`). Rename it to match your platform if needed (e.g. `dokploy-network`).
- All connection variables must be set in `backend/.env` or the platform's environment UI.
- The `api` service sets `TRUST_PROXY_HEADERS=True` for the platform ingress (Dokploy, Coolify, Nginx, PaaS). You do not add that variable to `.env`. Details: [Rate Limit Guide](rate-limit-guide.md).

**Run (from repository root):**

Start main API:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod up -d api
```

Run migration:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile migrate run --rm migrate
```

Start Celery Worker:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile worker up -d celery_worker
```

Start Celery Beat:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile scheduler up -d celery_beat
```

Start Flower (Observability):

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile observability up -d celery_flower
```

---

## 🖥️ native

> Full documentation: [deploy/native/README.md](../deploy/native/README.md)

**When to use:** You want to deploy on a **Linux VPS without Docker**, using Nginx as the reverse proxy and Supervisor to manage processes.

Based on: [FastAPI with Nginx and Gunicorn](https://dylancastillo.co/posts/fastapi-nginx-gunicorn.html)

**Directory structure:**

```
deploy/native/
├── logs/           # Log output directory
├── nginx/
│   └── nginx.conf  # Nginx reverse-proxy configuration
├── scripts/        # Bash wrapper scripts for each process
│   ├── backend-api
│   ├── backend-worker
│   └── backend-scheduler
└── supervisor/     # Supervisor program configurations
    ├── backend-api.conf
    ├── backend-worker.conf
    └── backend-scheduler.conf
```

**High-level steps:**

1. Install Nginx, Supervisor, Python 3.11, and Poetry on the server.
2. Clone the repository and run `poetry install` inside `backend/`.
3. Copy `backend/.env.example` → `backend/.env` and fill in production values. Nginx sits in front of Gunicorn, so add `TRUST_PROXY_HEADERS=True` to `.env` (it is not in `.env.example`). See the [Rate Limit Guide](rate-limit-guide.md).
4. Run `alembic upgrade head` to apply migrations.
5. Make the scripts in `deploy/native/scripts/` executable.
6. Symlink Supervisor configs to `/etc/supervisor/conf.d/`.
7. Symlink `deploy/native/nginx/nginx.conf` to `/etc/nginx/sites-enabled/fastapi-app` and remove the default site.

> [!IMPORTANT]
> See the [full native README](../deploy/native/README.md) for the exact commands with paths.

---

## CORS

CORS is a **browser** policy (fetch/XHR between origins). Native Android and iOS clients (OkHttp, URLSession), curl, Locust, and other backends **do not** apply `Access-Control-Allow-Origin`. Those clients are authenticated with JWT, not CORS.

This starter takes an API-first approach. The default is `CORS_ALLOW_ORIGINS=*` with `CORS_ALLOW_CREDENTIALS=false` — intentional, including for mobile apps.

Tighten CORS only if a **website** (admin UI, PWA) on another origin calls the API:

- Set `CORS_ALLOW_ORIGINS` to an explicit list, for example `https://admin.example.com`.
- Never combine `*` with `CORS_ALLOW_CREDENTIALS=true` (browsers reject that).
- **WebView:** if the WebView loads remote HTML, that page's origin counts. If the app calls the API from native code only, CORS still does not apply.

Variables: `CORS_ALLOW_ORIGINS`, `CORS_ALLOW_METHODS`, `CORS_ALLOW_HEADERS`, `CORS_ALLOW_CREDENTIALS`, `CORS_EXPOSE_HEADERS`, `CORS_MAX_AGE` (see [backend/.env.example](../backend/.env.example)).

---

## Common: Environment Variables

All deployment modes read from `backend/.env`. This file is never committed to version control.

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your production values
```

Key variables to configure before deploying:

| Variable                                              | Description                                                                                   |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `SECRET_KEY`                                          | App secret key — generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `POSTGRES_SERVER`                                     | Database host                                                                                 |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Database credentials                                                                          |
| `REDIS_CACHE_HOST` / `REDIS_CACHE_PASSWORD`           | Redis connection                                                                              |
| `REDIS_BROKER_HOST` / `REDIS_BROKER_PASSWORD`         | Celery broker Redis                                                                           |
| `FLOWER_BASIC_AUTH`                                   | Flower UI auth (`user:password`)                                                              |
| `ENVIRONMENT`                                         | Set to `production` for prod deployments                                                      |
| `CORS_ALLOW_ORIGINS`                                  | Browser origins allowed to call the API (`*` default; native apps ignore CORS)                |
| `LOG_FORMAT` / `LOG_TO_FILE` / `LOG_LEVEL`            | `text`+file by default; PaaS: `json` and `LOG_TO_FILE=false`                                  |
| `ACCESS_TOKEN_EXPIRE_MINUTES`                         | Access token TTL (default 15; refresh cookie stays `REFRESH_TOKEN_EXPIRE_DAYS`)               |

See [backend/.env.example](../backend/.env.example) for the full list.
