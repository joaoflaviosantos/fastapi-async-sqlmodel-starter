# Development Guide

This guide describes all available modes for running the project locally. Choose the one that best fits your workflow.

For production deployment, see the [Deployment Guide](deploy-guide.md).

---

## Overview

```
development/
├── compose/
│   ├── full-stack/    → Everything in Docker (databases + API + workers)
│   └── infra-only/    → Only databases in Docker; API runs on the host
└── native/            → Everything runs directly on the host (no Docker)
```

| Mode                                      | Best For                          | Docker Required | Hot Reload | IDE Debugger   |
| ----------------------------------------- | --------------------------------- | --------------- | ---------- | -------------- |
| [compose/full-stack](#-composefull-stack) | Isolated, consistent environment  | ✅              | ✅         | ⚠️ Remote only |
| [compose/infra-only](#-composeinfra-only) | Native API with local DBs         | ✅ (DBs only)   | ✅         | ✅             |
| [native](#-native)                        | Maximum performance, full control | ❌              | ✅         | ✅             |

---

## 🐳 compose/full-stack

> Full documentation: [development/compose/full-stack/README.md](../development/compose/full-stack/README.md)

**When to use:** You want to run everything — databases, API, and Celery services — inside Docker containers on your local machine, with hot-reload enabled via volume mounts.

**What's included:**

| Service         | Description                                        |
| --------------- | -------------------------------------------------- |
| `postgres`      | PostgreSQL 17 with pgvector                        |
| `redis`         | Redis Alpine                                       |
| `migrate`       | Runs `alembic upgrade head` once before API starts |
| `api`           | FastAPI via Uvicorn with `--reload`                |
| `celery_worker` | Celery Worker (source mounted)                     |
| `celery_beat`   | Celery Beat scheduler                              |
| `celery_flower` | Flower UI (auth required)                          |

**Prerequisites:**

- Docker and Docker Compose installed.
- `backend/.env` configured (copy from `backend/.env.example`).
- `FLOWER_BASIC_AUTH=user:password` set in `backend/.env`.

**Run (from repository root):**

Start main environment (Postgres, Redis, API):

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter up -d
```

Run migration:

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  --profile migrate run --rm migrate
```

Start Celery Worker:

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  --profile worker up -d celery_worker
```

Start Celery Beat:

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  --profile scheduler up -d celery_beat
```

Start Flower (Observability):

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  --profile observability up -d celery_flower
```

**Notes:**

- The `backend/` directory is mounted as a volume — code changes reflect immediately without rebuilding.
- Connection host variables (`POSTGRES_SERVER`, `REDIS_*_HOST`) are automatically overridden to point to the Docker service names. Your `.env` values for those are not used inside Docker.
- Host-published ports bind to `127.0.0.1` (API `8000`, Flower `5555`, Postgres, Redis). Use `http://127.0.0.1:8000`, not `localhost` (Windows often resolves `localhost` to IPv6).

---

## 🐳 compose/infra-only

> Full documentation: [development/compose/infra-only/README.md](../development/compose/infra-only/README.md)

**When to use:** You want Postgres and Redis running in Docker, but prefer to run the API and Celery directly on your host machine — for full IDE debugger support or faster startup.

**What's included:**

| Service    | Description                                               |
| ---------- | --------------------------------------------------------- |
| `postgres` | PostgreSQL 17 with pgvector (exposed on `127.0.0.1:5432`) |
| `redis`    | Redis Alpine (exposed on `127.0.0.1:6379`)                |

**Run (from repository root):**

```bash
docker compose --env-file backend/.env -f development/compose/infra-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter up -d
```

Then run the backend. **Option A — Quick start:**

```bash
python3 setup.py
```

Choose **1 – Local Development**. `Setup environment` appears only if `backend/.env` is missing required values; otherwise start FastAPI / Celery from that submenu. You can also run `python setup.py local`.

**Option B — Manual (from `backend/`):**

```bash
poetry run alembic upgrade head
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
# In another terminal:
poetry run celery -A src.worker worker --loglevel=info
```

**Notes:**

- Make sure `backend/.env` has `POSTGRES_SERVER=127.0.0.1` and `REDIS_CACHE_HOST=127.0.0.1` (copy `backend/.env.example` if you have no `.env` yet).
- Redis requires `REDIS_CACHE_PASSWORD` (Compose uses it for `--requirepass`).
- Compose publishes Postgres and Redis on IPv4 loopback only (`127.0.0.1`), so the host API does not hit IPv6 `localhost`.

---

## 🖥️ native

> Full documentation: [development/native/README.md](../development/native/README.md)

**When to use:** You want to run everything directly on your host machine without Docker — the fastest setup with the lowest overhead and full debugger support.

**Prerequisites:**

- Python 3.11+ and [Poetry](https://python-poetry.org/)
- PostgreSQL with pgvector extension installed locally
- Redis installed locally

> **Don't have Python/Poetry?** Use the install helper scripts:
>
> - **Linux**: `bash development/native/scripts/install_python.sh`
> - **Windows**: `development\native\scripts\install_python.bat`

**Quick start (recommended):**

```bash
python3 setup.py
```

Choose **1 – Local Development** (or `python setup.py local`). The Setup wizard runs only when `backend/.env` is incomplete.

**Manual setup (from `backend/`):**

```bash
poetry install
cp .env.example .env   # Edit with your local DB credentials
poetry run alembic upgrade head
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Tips:**

- Use [Honcho](https://honcho.readthedocs.io/) to manage multiple processes in one terminal.
- If you don't want to install Postgres/Redis locally, use `compose/infra-only` instead.

---

## Common: Environment Variables

All development modes use `backend/.env`. Start by copying the example:

```bash
cp backend/.env.example backend/.env
```

For local development, the key variables to set are:

| Variable               | Local Default                 |
| ---------------------- | ----------------------------- |
| `POSTGRES_SERVER`      | `127.0.0.1`                   |
| `POSTGRES_USER`        | `postgres`                    |
| `POSTGRES_PASSWORD`    | `postgres`                    |
| `POSTGRES_DB`          | `postgres`                    |
| `REDIS_CACHE_HOST`     | `127.0.0.1`                   |
| `REDIS_CACHE_PASSWORD` | `redis`                       |
| `REDIS_CACHE_DB`       | `0`                           |
| `REDIS_BROKER_HOST`    | empty (falls back to cache)   |
| `SECRET_KEY`           | generated by the CLI if empty |
| `ENVIRONMENT`          | `local`                       |

> For Docker-based modes (`compose/full-stack`, `compose/infra-only`), host variables like `POSTGRES_SERVER` are overridden automatically by the compose file.

See [backend/.env.example](../backend/.env.example) for the full list and descriptions.

---

## Further Reading

- [Backend README](../backend/README.md) — Manual backend setup instructions, migrations, and testing.
- [Celery Guide](celery-guide.md) — Celery worker configuration and Windows-specific notes.
- [Database Migration Guide](database-migration-guide.md) — Alembic workflow for schema changes.
- [Testing Guide](testing-guide.md) — Running the test suite with pytest.
- [Uvicorn Guide](uvicorn-guide.md) — Local Uvicorn, Compose, and native Gunicorn workers.
