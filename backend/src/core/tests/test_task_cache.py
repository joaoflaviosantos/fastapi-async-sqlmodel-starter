"""Celery cache clients belong to one invocation, not the API or another loop."""

# Built-in Dependencies
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

# Third-Party Dependencies
from celery import Celery
import pytest

# Local Dependencies
from src._overrides.celery.async_task import async_task
from src.core.utils import cache

pytestmark = pytest.mark.unit


@pytest.fixture
def task_app():
    with Celery(f"cache-test-{uuid4().hex}", set_as_current=False) as app:
        yield app


async def test_task_cache_is_lazy_and_keeps_api_client(monkeypatch, settings):
    api_client = AsyncMock()
    worker_client = AsyncMock()
    factory = Mock(return_value=worker_client)
    monkeypatch.setattr(cache, "client", api_client)
    monkeypatch.setattr(cache.Redis, "from_url", factory)

    assert cache.get_cache_client() is api_client
    async with cache.task_cache_context():
        pass
    factory.assert_not_called()

    async def child():
        assert cache.get_cache_client() is worker_client

    async with cache.task_cache_context():
        await asyncio.gather(child(), child())
        assert cache.get_cache_client() is worker_client
        worker_client.aclose.assert_not_awaited()
    factory.assert_called_once_with(
        str(settings.REDIS_CACHE_URL),
        encoding="utf8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    worker_client.aclose.assert_awaited_once()
    assert cache.get_cache_client() is api_client
    api_client.aclose.assert_not_awaited()


def test_cache_invalidation_from_successive_task_loops(monkeypatch, task_app, caplog):
    clients = [AsyncMock(), AsyncMock()]
    for client in clients:
        client.scan.return_value = (0, ["example:items:42:details"])
    factory = Mock(side_effect=clients)
    monkeypatch.setattr(cache, "client", None)
    monkeypatch.setattr(cache.Redis, "from_url", factory)

    @async_task(task_app, name=f"invalidate-{uuid4().hex}", shared=False, bind=True)
    async def invalidate(self):
        assert self.name.startswith("invalidate-")
        await cache._delete_keys_by_pattern("example:items:42:*")
        await cache._delete_keys_by_pattern("example:items:42:*")
        return "committed"

    assert invalidate.run() == "committed"
    assert invalidate.run() == "committed"
    assert factory.call_count == 2
    for client in clients:
        assert client.scan.await_count == 2
        client.scan.assert_awaited_with(cursor=0, match="example:items:42:*", count=100)
        assert client.delete.await_count == 2
        client.aclose.assert_awaited_once()
    assert cache.client is None
    assert cache.get_cache_client() is None
    assert "not initialized" not in caplog.text


@pytest.mark.parametrize("close_fails", [False, True])
def test_task_error_still_closes_cache_without_masking_original_error(
    monkeypatch, task_app, close_fails
):
    client = AsyncMock()
    if close_fails:
        client.aclose.side_effect = ConnectionError("close failed")
    monkeypatch.setattr(cache.Redis, "from_url", Mock(return_value=client))

    @async_task(task_app, name=f"fails-{uuid4().hex}", shared=False)
    async def fails():
        cache.get_cache_client()
        raise ValueError("task failed")

    with pytest.raises(ValueError, match="task failed"):
        fails.run()
    client.aclose.assert_awaited_once()
    assert cache._task_cache_state.get() is None


def test_redis_unavailable_does_not_fail_task(monkeypatch, task_app):
    client = AsyncMock()
    client.scan.side_effect = ConnectionError("offline")
    monkeypatch.setattr(cache.Redis, "from_url", Mock(return_value=client))

    @async_task(task_app, name=f"offline-{uuid4().hex}", shared=False)
    async def process_items():
        await cache._delete_keys_by_pattern("example:items:42:*")
        return {"processed": 1}

    assert process_items.run() == {"processed": 1}
    client.scan.assert_awaited_once()
    client.aclose.assert_awaited_once()


def test_threaded_task_loops_isolate_cache_clients(monkeypatch, task_app):
    api_client = AsyncMock()
    worker_clients = []
    start = Barrier(2)

    def create(*args, **kwargs):
        client = AsyncMock()
        worker_clients.append(client)
        return client

    monkeypatch.setattr(cache, "client", api_client)
    monkeypatch.setattr(cache.Redis, "from_url", create)

    @async_task(task_app, name=f"threads-{uuid4().hex}", shared=False)
    async def operation():
        client = cache.get_cache_client()
        start.wait(timeout=5)
        await asyncio.sleep(0)
        assert cache.get_cache_client() is client
        return client

    # Resolve the Celery proxy before starting concurrent calls to its run method.
    run = operation.run
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run)
        second = pool.submit(run)
        assert first.result(timeout=10) is not second.result(timeout=10)
    assert len(worker_clients) == 2
    for client in worker_clients:
        client.aclose.assert_awaited_once()
    assert cache.client is api_client
    api_client.aclose.assert_not_awaited()
