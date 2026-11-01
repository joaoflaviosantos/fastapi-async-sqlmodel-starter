# Built-in Dependencies
import asyncio
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar
from functools import wraps

# Third-Party Dependencies
from celery import Celery, Task

# Local Dependencies
from src.core.utils.cache import task_cache_context

_P = ParamSpec("_P")
_R = TypeVar("_R")


def async_task(
    app: Celery, *args: Any, **kwargs: Any
) -> Callable[[Callable[_P, Coroutine[Any, Any, _R]]], Task]:
    """
    Decorator that turns an async function into a synchronous Celery task.

    Uses ``asyncio.run()`` instead of ``asgiref.AsyncToSync`` so that every
    task invocation gets its own *fresh*, isolated event loop.  This prevents
    the classic "Future attached to a different loop" / "Event loop is closed"
    errors that arise when async Redis (or any other async I/O) resources
    initialised in one loop are later accessed from a different loop.
    Cache clients are opened lazily in a task-local context and closed
    before that invocation's loop exits; API lifespan globals are never replaced.
    """

    def _decorator(func: Callable[_P, Coroutine[Any, Any, _R]]) -> Task:
        async def _run(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            async with task_cache_context():
                return await func(*args, **kwargs)

        @app.task(*args, **kwargs)
        @wraps(func)
        def _decorated(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return asyncio.run(_run(*args, **kwargs))

        return _decorated

    return _decorator
