"""The worker checks Redis synchronously without sharing an async cache pool."""

# Built-in Dependencies
from unittest.mock import MagicMock, Mock

# Third-Party Dependencies
import pytest

# Local Dependencies
from src import worker
from src.core.utils import cache

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("failure_at", [None, "create", "ping"])
def test_worker_ready_checks_redis_and_preserves_task_cache_lifecycle(
    monkeypatch, settings, failure_at
):
    manager = MagicMock()
    client = manager.__enter__.return_value
    factory = Mock(return_value=manager)
    if failure_at == "create":
        factory.side_effect = ValueError("invalid connection settings")
    elif failure_at == "ping":
        client.ping.side_effect = ConnectionError("unavailable")
    logger = Mock()
    async_factory = Mock(side_effect=AssertionError("startup must not create an async pool"))
    monkeypatch.setattr(worker.redis, "from_url", factory)
    monkeypatch.setattr(worker, "logger_worker", logger)
    monkeypatch.setattr(cache.Redis, "from_url", async_factory)
    api_client, api_pool = cache.client, cache.pool

    worker.on_worker_ready(sender="test-worker")

    factory.assert_called_once_with(
        str(settings.REDIS_CACHE_URL), socket_connect_timeout=5, socket_timeout=5
    )
    if failure_at != "create":
        client.ping.assert_called_once_with()
        manager.__exit__.assert_called_once()
    if failure_at is None:
        logger.info.assert_any_call("Redis cache reachability confirmed at worker boot")
        logger.exception.assert_not_called()
    else:
        logger.exception.assert_called_once_with("Redis cache health-check failed at worker boot")
    logger.info.assert_any_call("Worker is READY and accepting tasks: test-worker")
    async_factory.assert_not_called()
    assert cache.client is api_client
    assert cache.pool is api_pool
