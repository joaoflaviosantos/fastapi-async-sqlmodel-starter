---
name: celery
description: Create or change Celery tasks.py, register modules on the worker, and use async_task plus local_session. Use when adding background jobs, Beat entries, or email/async work off the request path.
---

# Celery tasks

Follow `AGENTS.md`. This skill is the recipe for `tasks.py` and worker registration.

Copy-target: `.agents/examples/subapp/tasks.py`. Worker registration (live): `backend/src/worker.py`. Decorator: `src._overrides.celery.async_task.async_task`. Session: `src.core.db.session.local_session`.

Do not copy `backend/src/apps/system/users/tasks.py` for a new resource (that is the welcome-email product task). Do not add `.agents/examples/subapp/tasks` to `include`.

## Where tasks live

Colocate `tasks.py` in the subapp that owns the work (`src.apps.<app>.<subapp>.tasks`). Shared samples already on the worker: `src.apps.system.tasks.tasks`, `src.apps.system.users.tasks`.

## Define a task

```python
from uuid import UUID

from src._overrides.celery.async_task import async_task
from src.core.db.session import local_session
from src.worker import app

@async_task(app, name="notify_item_created", bind=True, max_retries=3)
async def notify_item_created(self, item_id: UUID) -> dict:
    try:
        async with local_session() as session:
            ...
        return {"status": "success", "item_id": str(item_id)}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

- Always `@async_task`, not `@app.task`.
- Give an explicit `name=` for Beat and callers.
- Open the DB with `local_session()`, never `async_get_db` (that is a FastAPI dependency).
- Log with `logger_worker` from `src.core.logger`.

## Cache in tasks

- Use `get_cache_client()` from `src.core.utils.cache` instead of accessing `cache.client` directly.
- `@async_task` manages the cache client's lifecycle. Do not initialize/close it manually or share it between task invocations.

When changing cache lifecycle behavior, read the [worker cache guide](../../../docs/celery-guide.md#redis-cache-in-worker-tasks).

## Register

After copying into `apps/`, add the **apps** module to `include=[...]` in `backend/src/worker.py`:

```python
include=[
    "src.apps.system.tasks.tasks",
    "src.apps.system.users.tasks",
    "src.apps.<app>.<subapp>.tasks",
]
```

Periodic jobs: `app.conf.beat_schedule` in the same file (`task=` is the explicit task name).

## Do not

- Do not introduce tenant orchestrators, `async_shared_task`, or `async_tenant_task` — this project is a single schema.
- Do not forget `include`; autodiscover alone is not enough for a new module.
