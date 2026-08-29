# Development — Docker (Infrastructure Only)

Use this when you want to **run only the databases in Docker** while running the API and Celery processes directly on your host machine (e.g. using your IDE's debugger or `uvicorn` from the terminal).

## What's included

| Service    | Description                       |
| ---------- | --------------------------------- |
| `postgres` | pgvector/pgvector (PostgreSQL 17) |
| `redis`    | Redis Alpine                      |

## How to run

### 1. Start the infrastructure

From the **repository root**:

```bash
docker compose --env-file backend/.env -f development/compose/infra-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter up -d
```

### 2. Run the backend

**Option A — Quick start via `setup.py` (recommended):**

```bash
python3 setup.py
```

Choose **1 – Local Development** (or `python setup.py local`). Setup runs only if `backend/.env` is missing required values.

**Option B — Manual (from `backend/`):**

```bash
cd backend

# Run migrations
poetry run alembic upgrade head

# Start the API
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal — start the Celery worker
poetry run celery -A src.worker worker --loglevel=info

# In another terminal — start the Celery beat scheduler
poetry run celery -A src.worker beat --loglevel=info
```

## Notes

- Published ports bind to IPv4 loopback (`127.0.0.1`), not `localhost` / IPv6. Postgres is `127.0.0.1:5432` (or `$POSTGRES_PORT`); Redis is `127.0.0.1:6379` (or `$REDIS_CACHE_PORT`) with `REDIS_CACHE_PASSWORD` from `backend/.env`.
- Make sure your `backend/.env` has `POSTGRES_SERVER=127.0.0.1` and `REDIS_CACHE_HOST=127.0.0.1`.
