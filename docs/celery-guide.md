# Celery Guide

## Overview

Celery is a distributed task queue system for Python, used in this project for handling background tasks asynchronously. Combined with the `async_task` decorator, it supports full async/await operations, enabling seamless integration with the async database (SQLModel/SQLAlchemy) and Redis connections used throughout the application.

## Introduction to Celery

[Celery](https://docs.celeryq.dev/en/stable/) is a robust, production-ready task queue that supports scheduling, retries, and result backends. In this project, it uses **Redis** as the message broker and **PostgreSQL** as the result backend.

### Key Features

- **Distributed Task Queue:** Celery enables efficient distribution of tasks across multiple workers.
- **Async Task Support:** Through the custom `async_task` decorator (`src/_overrides/celery/async_task.py`), async/await coroutines are fully supported as Celery tasks.
- **Scheduled Tasks (Beat):** Celery Beat provides periodic task scheduling (e.g., health checks every 30 seconds).
- **Result Backend:** Task results are persisted in PostgreSQL for tracking and auditing.
- **Retry Mechanism:** Built-in retry support with configurable backoff strategies.
- **FastAPI Compatibility:** Seamless integration with the FastAPI async ecosystem.

## Architecture

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  FastAPI    │─────▶│    Redis     │◀─────│   Celery    │
│  (Producer) │       │  (Broker)   │       │  (Worker)   │
└─────────────┘       └─────────────┘       └──────┬──────┘
                                                   │
                                            ┌──────▼──────┐
                                            │  PostgreSQL │
                                            │  (Results)  │
                                            └─────────────┘
```

## Configuration

The Celery application is configured in `src/worker.py`:

- **Broker:** `settings.REDIS_BROKER_URL` (Redis)
- **Result Backend:** `settings.POSTGRES_CELERY_URI` (PostgreSQL, scheme `db+postgresql://`)
- **Timezone:** UTC
- **Default Queue:** `default`
- **Concurrency:** 4 workers

### Environment Variables

| Variable                | Default                            | Description                      |
| ----------------------- | ---------------------------------- | -------------------------------- |
| `REDIS_BROKER_HOST`     | (falls back to `REDIS_CACHE_HOST`) | Redis broker host                |
| `REDIS_BROKER_PORT`     | `6379`                             | Redis broker port                |
| `REDIS_BROKER_USERNAME` | ``                                 | Redis broker username            |
| `REDIS_BROKER_PASSWORD` | ``                                 | Redis broker password            |
| `REDIS_BROKER_USE_SSL`  | `False`                            | Enable SSL for broker connection |

The `POSTGRES_CELERY_URI` is automatically derived from the existing PostgreSQL settings (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`).

## Running the Celery Worker

To start the Celery worker:

**Linux / macOS:**

```bash
poetry run celery -A src.worker:app worker --loglevel=info
```

**Windows** (requires thread pool to prevent asyncio event loop deadlocks):

```bash
poetry run celery -A src.worker:app worker --loglevel=info -P threads
```

> [!NOTE]
> On Windows, the default `prefork` pool is not compatible with asyncio-based tasks. The `-P threads` flag switches to the thread pool, allowing each worker thread to manage its own event loop safely.

## Running Celery Beat (Scheduler)

To start the periodic task scheduler:

```bash
poetry run celery -A src.worker:app beat --loglevel=info
```

## Running Worker + Beat Together (Development)

For development convenience, you can run both in a single process:

**Linux / macOS:**

```bash
poetry run celery -A src.worker:app worker --beat --loglevel=info
```

**Windows:**

```bash
poetry run celery -A src.worker:app worker --beat --loglevel=info -P threads
```

## Creating Async Tasks

All tasks in this project use the `@async_task` decorator to support async/await:

```python
from src._overrides.celery.async_task import async_task
from src.core.db.session import local_session
from src.worker import app

@async_task(app, name="my_task_name", bind=True, max_retries=3)
async def my_task(self, param1: str, param2: str) -> dict:
    # You can use async DB sessions, async Redis, etc.
    async with local_session() as db:
        # ... async database operations
        pass

    return {"status": "success"}
```

### How It Works

The `async_task` decorator (in `src/_overrides/celery/async_task.py`) uses `asyncio.run()` to execute each invocation on a fresh event loop. Cache resources are scoped to that invocation and closed before its loop exits. This allows you to:

- Use `async/await` syntax in your tasks
- Open an async database session with `local_session()`
- Use `redis.asyncio` for Redis operations
- Call any async library or function

### Redis Cache in Worker Tasks

The API creates its cache client in the lifespan defined in `src/core/setup.py`. A worker does not run that lifespan. Its `on_worker_ready` hook performs a synchronous Redis `PING` using `REDIS_CACHE_URL`, with bounded connection/read timeouts, and closes the temporary client immediately. Connectivity failures are logged without preventing worker startup. This check does not create an asynchronous pool or initialize the cache client used by tasks.

Every `@async_task` invocation opens a `task_cache_context`. Use `get_cache_client()` from `src.core.utils.cache` when accessing the cache in shared API/worker code. Inside a task, the client is created lazily from `REDIS_CACHE_URL`, shared with child coroutines, and closed in `finally`, including failures and retries. Outside a task, the helper returns the API lifespan client. Tasks that never access the cache create no Redis connections.

```python
from src.core.utils.cache import get_cache_client

async def invalidate_item(item_id: int) -> None:
    client = get_cache_client()
    if client is not None:
        await client.delete(f"example:items:{item_id}")
```

The cache decorator and SCAN-based invalidation helper also resolve the client through this context. Do not assign a worker client to the process-global `cache.client` or initialize an asynchronous cache pool at worker boot: different task invocations use different event loops, and concurrent worker threads must not share those connections. API lifespan initialization remains responsible for the API's pool.

Cache connection and read/write timeouts are bounded in worker tasks. The cache decorator and pattern invalidation retain their fail-open behavior when Redis is unavailable; direct Redis operations should apply the error policy required by their caller. This resource management concerns application caching, separate from the Celery broker connection.

## Registered Tasks

| Task Name                  | Module                        | Type       | Description                                                              |
| -------------------------- | ----------------------------- | ---------- | ------------------------------------------------------------------------ |
| `send_welcome_email`       | `src.apps.system.users.tasks` | On-demand  | Sends welcome email when a new user is created (log simulation)          |
| `sample_background_task`   | `src.apps.system.tasks.tasks` | On-demand  | Sample long-running job used by the tasks HTTP API                       |
| `check_application_health` | `src.apps.system.tasks.tasks` | Beat (30s) | Periodic check of PostgreSQL, Redis, and `GET /health` plus `GET /ready` |

## Calling Tasks

### From FastAPI endpoints or services:

```python
from src.apps.system.users.tasks import send_welcome_email

# Async dispatch (non-blocking)
send_welcome_email.delay("user@example.com", "username")

# With options
send_welcome_email.apply_async(
    args=["user@example.com", "username"],
    countdown=10,  # delay 10 seconds
    queue="default",
)
```

## Monitoring

### Flower (Web UI)

You can use [Flower](https://flower.readthedocs.io/) for real-time monitoring:

```bash
poetry run celery -A src.worker:app flower --port=5555
```

Then access `http://localhost:5555` in your browser.

### CLI Inspection

```bash
# List active tasks
poetry run celery -A src.worker:app inspect active

# List registered tasks
poetry run celery -A src.worker:app inspect registered

# List scheduled tasks
poetry run celery -A src.worker:app inspect scheduled
```

---

[Back to backend README](../backend/README.md)
