"""A task invalidates an HTTP cache without running the API lifespan."""

# Built-in Dependencies
import asyncio
from unittest.mock import patch
from uuid import uuid4

# Third-Party Dependencies
from celery import Celery
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
import pytest

# Local Dependencies
from src._overrides.celery.async_task import async_task
from src.core.utils import cache

pytestmark = pytest.mark.integration


async def test_worker_invalidates_api_cache_in_successive_event_loops(client):
    api_client = cache.client
    prefix = f"test:task-cache:{uuid4().hex}:items"
    cache_key = f"{prefix}:42"
    other_key = f"test:task-cache:{uuid4().hex}:other"
    state = {"value": 1}
    worker_clients = []
    worker_loops = []
    application = FastAPI()

    @application.get("/items/{item_id}")
    @cache.cache(key_prefix=prefix, resource_id_name="item_id")
    async def read_item(request: Request, item_id: int):
        return {"id": item_id, "value": state["value"]}

    with Celery(f"cache-test-{uuid4().hex}", set_as_current=False) as task_app:

        @async_task(task_app, name=f"invalidate-{uuid4().hex}", shared=False, bind=True)
        async def invalidate(self):
            assert self.name.startswith("invalidate-")
            assert cache.client is None
            worker_clients.append(cache.get_cache_client())
            worker_loops.append(asyncio.get_running_loop())
            await cache._delete_keys_by_pattern(f"{prefix}:*")

        await api_client.set(other_key, "preserve", ex=60)
        try:
            async with AsyncClient(
                transport=ASGITransport(app=application), base_url="http://test"
            ) as http:
                for _ in range(2):
                    previous_value = state["value"]
                    first = await http.get("/items/42")
                    assert first.status_code == 200
                    assert first.json()["value"] == previous_value
                    assert await api_client.exists(cache_key)
                    state["value"] += 1
                    cached = await http.get("/items/42")
                    assert cached.json()["value"] == previous_value
                    with patch.object(cache, "client", None):
                        await asyncio.to_thread(invalidate.run)
                    assert not await api_client.exists(cache_key)
                    refreshed = await http.get("/items/42")
                    assert refreshed.json()["value"] == state["value"]
                    assert await api_client.get(other_key) == "preserve"
            assert worker_clients[0] is not worker_clients[1]
            assert all(worker is not api_client for worker in worker_clients)
            assert worker_loops[0] is not worker_loops[1]
            assert cache.get_cache_client() is api_client
            assert await api_client.ping()
        finally:
            await api_client.delete(cache_key, other_key)
