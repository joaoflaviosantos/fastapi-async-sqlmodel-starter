# Built-in Dependencies
from typing import Any, AsyncIterator, Callable, Dict, List, Tuple, Union
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import functools
import json
import re

# Third-Party Dependencies
from redis.asyncio import Redis, ConnectionPool
from fastapi.encoders import jsonable_encoder
from fastapi import Request

# Local Dependencies
from src.core.exceptions.cache_exceptions import (
    CacheIdentificationInferenceError,
    InvalidRequestError,
)
from src.core.logger import logger_redis
from src.core.config import settings

pool: ConnectionPool | None = None
client: Redis | None = None


@dataclass
class _TaskCacheState:
    # Child coroutines inherit this same state so the parent can close the client.
    client: Redis | None = None


_task_cache_state: ContextVar[_TaskCacheState | None] = ContextVar(
    "worker_task_cache_state", default=None
)


def get_cache_client() -> Redis | None:
    """Use this task's lazy client, or the API lifespan client outside a task."""
    state = _task_cache_state.get()
    if state is None:
        return client
    if state.client is None:
        state.client = Redis.from_url(
            str(settings.REDIS_CACHE_URL),
            encoding="utf8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return state.client


@asynccontextmanager
async def task_cache_context() -> AsyncIterator[None]:
    """Own a cache client for one Celery invocation, never a process-global loop."""
    state = _TaskCacheState()
    token = _task_cache_state.set(state)
    try:
        yield
    finally:
        _task_cache_state.reset(token)
        if state.client is not None:
            try:
                await state.client.aclose()
            except Exception:
                logger_redis.exception("Failed to close task Redis cache client.")


def _stable_cache_value(value: Any) -> Any:
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, default=str)
    if isinstance(value, (list, tuple)):
        return json.dumps(value, sort_keys=True, default=str)
    return value


def _infer_resource_id(
    kwargs: Dict[str, Any], resource_id_type: Union[type, Tuple[type, ...]]
) -> Any:
    """Last kwarg whose name contains ``id`` and whose value matches ``resource_id_type``."""
    resource_id: Any | None = None
    for arg_name, arg_value in kwargs.items():
        if "id" not in arg_name:
            continue
        if isinstance(arg_value, resource_id_type):
            resource_id = arg_value
    if resource_id is None:
        raise CacheIdentificationInferenceError
    return resource_id


def _extract_data_inside_brackets(input_string: str) -> List[str]:
    return re.findall(r"{(.*?)}", input_string)


def _construct_data_dict(data_inside_brackets: List[str], kwargs: Dict[str, Any]) -> Dict[str, Any]:
    return {key: _stable_cache_value(kwargs[key]) for key in data_inside_brackets}


def _format_prefix(prefix: str, kwargs: Dict[str, Any]) -> str:
    data_inside_brackets = _extract_data_inside_brackets(prefix)
    data_dict = _construct_data_dict(data_inside_brackets, kwargs)
    return prefix.format(**data_dict)


def _format_extra_data(
    to_invalidate_extra: Dict[str, str], kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    formatted_extra = {}
    for prefix, id_template in to_invalidate_extra.items():
        formatted_prefix = _format_prefix(prefix, kwargs)
        placeholders = _extract_data_inside_brackets(id_template)
        extra_id = kwargs[placeholders[0]] if placeholders else kwargs[id_template]
        formatted_extra[formatted_prefix] = extra_id
    return formatted_extra


def _as_scan_pattern(pattern: str) -> str:
    if pattern.endswith("*"):
        return pattern
    return f"{pattern}*"


async def _delete_keys_by_pattern(pattern: str) -> None:
    """Delete Redis keys matching ``pattern`` via SCAN. Stop only when the cursor is 0."""
    cache_client = get_cache_client()
    if cache_client is None:
        logger_redis.warning("Redis cache client is not initialized; skip pattern delete.")
        return

    cursor = 0
    while True:
        try:
            cursor, keys = await cache_client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await cache_client.delete(*keys)
            if cursor == 0:
                break
        except Exception as exc:
            logger_redis.exception(f"Error in SCAN delete for pattern '{pattern}': {exc}")
            break


def cache(
    key_prefix: str,
    resource_id_name: str | None = None,
    expiration: int = 3600,
    resource_id_type: Union[type, Tuple[type, ...]] = int,
    to_invalidate_extra: Dict[str, Any] | None = None,
    pattern_to_invalidate_extra: List[str] | None = None,
) -> Callable:
    """
    Cache decorator for FastAPI endpoints (Redis).

    GET reads/writes ``{prefix}:{resource_id}``. Other methods run the handler first,
    then delete that item key (if a resource id is known) and optional extra keys/patterns.

    Redis failures fail open: the handler still runs. Invalidation failures are logged
    and do not hide service errors. ``InvalidRequestError`` (invalidate on GET) and
    ``CacheIdentificationInferenceError`` remain programmer errors.

    POST/create may omit ``resource_id_name`` and only pass ``pattern_to_invalidate_extra``.
    """

    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def inner(request: Request, *args: Any, **kwargs: Any) -> Any:
            if request.method == "GET":
                if to_invalidate_extra is not None or pattern_to_invalidate_extra is not None:
                    raise InvalidRequestError

            resource_id: Any | None = None
            if resource_id_name:
                resource_id = kwargs[resource_id_name]
            elif request.method == "GET":
                resource_id = _infer_resource_id(kwargs=kwargs, resource_id_type=resource_id_type)

            formatted_key_prefix = _format_prefix(key_prefix, kwargs)
            cache_key = f"{formatted_key_prefix}:{resource_id}" if resource_id is not None else None
            cache_client = get_cache_client()

            if request.method == "GET":
                if cache_key is None:
                    raise CacheIdentificationInferenceError
                if cache_client is None:
                    logger_redis.warning(
                        "Redis cache client is not initialized; skipping cache for GET."
                    )
                    return await func(request, *args, **kwargs)
                try:
                    cached_data = await cache_client.get(cache_key)
                    if cached_data:
                        return json.loads(cached_data)
                except Exception as exc:
                    logger_redis.exception(f"Redis GET failed for '{cache_key}': {exc}")
                    return await func(request, *args, **kwargs)

                result = await func(request, *args, **kwargs)
                try:
                    serialized = json.dumps(jsonable_encoder(result))
                    await cache_client.set(cache_key, serialized, ex=expiration)
                except Exception as exc:
                    logger_redis.exception(f"Redis SETEX failed for '{cache_key}': {exc}")
                return result

            result = await func(request, *args, **kwargs)
            if cache_client is None:
                logger_redis.warning(
                    "Redis cache client is not initialized; skipping cache invalidation."
                )
                return result
            try:
                if cache_key is not None:
                    await cache_client.delete(cache_key)
                if to_invalidate_extra is not None:
                    formatted_extra = _format_extra_data(to_invalidate_extra, kwargs)
                    for extra_prefix, extra_id in formatted_extra.items():
                        await cache_client.delete(f"{extra_prefix}:{extra_id}")
                if pattern_to_invalidate_extra is not None:
                    for pattern in pattern_to_invalidate_extra:
                        formatted_pattern = _format_prefix(pattern, kwargs)
                        await _delete_keys_by_pattern(_as_scan_pattern(formatted_pattern))
            except Exception as exc:
                logger_redis.exception(f"Redis cache invalidation failed: {exc}")
            return result

        return inner

    return wrapper
