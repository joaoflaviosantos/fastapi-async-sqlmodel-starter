# Built-in Dependencies
import platform
import asyncio
from typing import Any

# Third-Party Dependencies
import redis
from sqlalchemy.pool import NullPool
from celery.signals import (
    celeryd_init,
    celeryd_after_setup,
    worker_ready,
    worker_shutting_down,
)
from celery import Celery

# Local Dependencies
from src.core.utils.log import log_system_info
from src.core.logger import logger_worker
from src.core.config import settings

# Event loop policy configuration per OS
if platform.system() == "Linux":
    import uvloop

    # On Linux, use uvloop for better performance
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
elif platform.system() == "Windows":
    # On Windows with gevent (-P gevent), only set the policy — do NOT pre-create
    # a persistent event loop. asgiref.AsyncToSync manages its own loop per call.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# ----------------------------------------
# ---------- CELERY APPLICATION ----------
# ----------------------------------------
app = Celery(
    "worker",
    broker=str(settings.REDIS_BROKER_URL),
    backend=str(settings.POSTGRES_CELERY_URI),
    include=[
        "src.apps.system.tasks.tasks",
        "src.apps.system.users.tasks",
    ],
)

# Automatically discover tasks
app.autodiscover_tasks()

# Timezone Configuration
app.conf.timezone = "UTC"

# Concurrency Configuration
# NOTE: On Windows, run with: celery -A src.worker worker --loglevel=info -P threads
# NOTE: On Linux, run with: celery -A src.worker worker --loglevel=info
if platform.system() == "Windows":
    app.conf.worker_concurrency = 4
else:
    app.conf.worker_concurrency = 4

# Task Processing Settings
app.conf.task_acks_late = True  # Acknowledge task only after successful processing
app.conf.task_reject_on_worker_lost = True
app.conf.worker_send_task_events = True
app.conf.task_ignore_result = False  # Don't ignore results
app.conf.worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks

# Serialization Configuration
app.conf.accept_content = ["json"]
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"

# Queue Configuration
app.conf.task_default_queue = "default"

# Retry broker connection on startup (Celery 6.0+ compatibility)
app.conf.broker_connection_retry_on_startup = True

# Database (Result Backend) Configuration
app.conf.database_engine_options = {
    "echo": False,
    "poolclass": NullPool,
    "connect_args": {
        "sslmode": "disable",
        "sslrootcert": "",
        "application_name": f"{settings.PROJECT_NAME} - celery_worker",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
    },
}
app.conf.database_table_schemas = {
    "task": "public",
    "group": "public",
}
app.conf.database_table_names = {
    "task": "system_task_meta",
    "group": "system_taskset_meta",
}
# Task tracking and result settings
app.conf.task_track_started = True
app.conf.result_extended = True
app.conf.result_backend_always_retry = True
app.conf.result_expires = 24 * 3600 * 7  # 7 days


# ----------------------------------------
# ------------ CELERY BEAT ---------------
# ----------------------------------------
app.conf.beat_schedule = {
    "check-application-health-every-30-seconds": {
        "task": "check_application_health",
        "schedule": 30.0,
        "options": {"queue": "default"},
    },
}


# ----------------------------------------
# ------- WORKER STARTUP SIGNALS ---------
# ----------------------------------------
@celeryd_init.connect
def configure_worker(
    sender: Any = None,
    instance: Any = None,
    conf: Any = None,
    options: Any = None,
    **kwargs: Any,
) -> None:
    logger_worker.info(f"Worker setup started: {sender}")
    log_system_info(logger=logger_worker)


@celeryd_after_setup.connect
def setup_direct_queue(
    sender: Any = None, instance: Any = None, conf: Any = None, **kwargs: Any
) -> None:
    logger_worker.info(f"Worker setup complete: {sender}")


@worker_ready.connect
def on_worker_ready(sender: Any = None, **kwargs: Any) -> None:
    # NOTE: On Windows, Celery's 'celery@hostname ready.' banner text may not appear
    # in the terminal output due to stdout interleaving from the subprocess shell.
    # This signal is the reliable indicator that the worker is ready to accept tasks.
    # Check connectivity without creating an async pool in the startup loop.
    # async_task creates and closes its own cache client in each invocation.
    try:
        with redis.from_url(
            str(settings.REDIS_CACHE_URL), socket_connect_timeout=5, socket_timeout=5
        ) as client:
            client.ping()
        logger_worker.info("Redis cache reachability confirmed at worker boot")
    except Exception:
        logger_worker.exception("Redis cache health-check failed at worker boot")

    logger_worker.info(f"Worker is READY and accepting tasks: {sender}")


@worker_shutting_down.connect
def on_worker_shutting_down(
    sender: Any = None, sig: Any = None, how: Any = None, exitcode: Any = None, **kwargs: Any
) -> None:
    logger_worker.info(f"Worker shutting down — sig={sig}, how={how}")
