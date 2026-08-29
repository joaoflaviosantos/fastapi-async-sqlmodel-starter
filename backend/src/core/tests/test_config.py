# Built-in Dependencies
import re
from pathlib import Path

# Third-Party Dependencies
import pytest
from pydantic import ValidationError

# Local Dependencies
from src.core.common.enums import EmailSenderType
from src.core.config import (
    EmailSettings,
    LoggingSettings,
    PostgresSettings,
    RedisBrokerSettings,
    RedisCacheSettings,
    RedisRateLimiterSettings,
)

pytestmark = pytest.mark.unit

_CONFIG_PY = Path(__file__).resolve().parents[1] / "config.py"
_ENV_EXAMPLE = Path(__file__).resolve().parents[3] / ".env.example"
_CONFIG_KEY_RE = re.compile(r'config\("([A-Z0-9_]+)"')
_ENV_EXAMPLE_KEY_RE = re.compile(r"^([A-Z][A-Z0-9_]*)=")

EXAMPLE_ONLY_KEYS = frozenset({"FLOWER_BASIC_AUTH"})
KEYS_WITHOUT_STATIC_DEFAULT = frozenset({"SECRET_KEY", "USER_SYSTEM_PASSWORD"})

EXPECTED_SETTINGS_FIELDS = frozenset(
    {
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "ALGORITHM",
        "API_BASE_URL",
        "APP_VERSION",
        "CLIENT_CACHE_MAX_AGE",
        "CONTACT_EMAIL",
        "CONTACT_NAME",
        "CORS_ALLOW_CREDENTIALS",
        "CORS_ALLOW_HEADERS",
        "CORS_ALLOW_METHODS",
        "CORS_ALLOW_ORIGINS",
        "CORS_EXPOSE_HEADERS",
        "CORS_MAX_AGE",
        "DEFAULT_RATE_LIMIT_LIMIT",
        "DEFAULT_RATE_LIMIT_PERIOD",
        "EMAILS_FROM_EMAIL",
        "EMAILS_FROM_NAME",
        "EMAIL_SENDER",
        "ENVIRONMENT",
        "LICENSE_NAME",
        "LOG_FORMAT",
        "LOG_LEVEL",
        "LOG_TO_FILE",
        "POSTGRES_ASYNC_URI",
        "POSTGRES_CELERY_URI",
        "POSTGRES_DB",
        "POSTGRES_PASSWORD",
        "POSTGRES_POOL_SIZE",
        "POSTGRES_PORT",
        "POSTGRES_SERVER",
        "POSTGRES_USER",
        "PROJECT_DESCRIPTION",
        "PROJECT_NAME",
        "REDIS_BROKER_DB",
        "REDIS_BROKER_HOST",
        "REDIS_BROKER_PASSWORD",
        "REDIS_BROKER_PORT",
        "REDIS_BROKER_URL",
        "REDIS_BROKER_USERNAME",
        "REDIS_BROKER_USE_SSL",
        "REDIS_CACHE_DB",
        "REDIS_CACHE_HOST",
        "REDIS_CACHE_PASSWORD",
        "REDIS_CACHE_PORT",
        "REDIS_CACHE_URL",
        "REDIS_CACHE_USERNAME",
        "REDIS_CACHE_USE_SSL",
        "REDIS_HASH_SYSTEM_AUTH_VALID_USERNAMES",
        "REDIS_RATE_LIMIT_DB",
        "REDIS_RATE_LIMIT_HOST",
        "REDIS_RATE_LIMIT_PASSWORD",
        "REDIS_RATE_LIMIT_PORT",
        "REDIS_RATE_LIMIT_URL",
        "REDIS_RATE_LIMIT_USERNAME",
        "REDIS_RATE_LIMIT_USE_SSL",
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "SECRET_KEY",
        "SMTP_HOST",
        "SMTP_PASSWORD",
        "SMTP_PORT",
        "SMTP_USER",
        "TIER_NAME_DEFAULT",
        "TRUST_PROXY_HEADERS",
        "USER_FIRST_ADMIN_EMAIL",
        "USER_FIRST_ADMIN_ID",
        "USER_FIRST_ADMIN_NAME",
        "USER_FIRST_ADMIN_PASSWORD",
        "USER_FIRST_ADMIN_USERNAME",
        "USER_SYSTEM_EMAIL",
        "USER_SYSTEM_ID",
        "USER_SYSTEM_NAME",
        "USER_SYSTEM_PASSWORD",
        "USER_SYSTEM_USERNAME",
        "USER_TEST_EMAIL",
        "USER_TEST_NAME",
        "USER_TEST_PASSWORD",
        "USER_TEST_USERNAME",
        "WEB_CONCURRENCY",
    }
)

EXPECTED_CONFIG_SNIPPETS = frozenset(
    {
        'config("PROJECT_NAME", default="FastAPI Async SQLModel Starter")',
        'config("PROJECT_DESCRIPTION", default=None)',
        'config("APP_VERSION", default="0.0.1")',
        'config("LICENSE_NAME", default=None)',
        'config("CONTACT_NAME", default=None)',
        'config("CONTACT_EMAIL", default=None)',
        'config("API_BASE_URL", default="http://127.0.0.1:8000")',
        'config("WEB_CONCURRENCY", default=1)',
        'config("ALGORITHM", default="HS256")',
        'config("ACCESS_TOKEN_EXPIRE_MINUTES", default=15)',
        'config("REFRESH_TOKEN_EXPIRE_DAYS", default=7)',
        'config("SMTP_HOST", default=None)',
        'config("SMTP_PORT", default=587)',
        'config("SMTP_USER", default=None)',
        'config("SMTP_PASSWORD", default=None)',
        'config("EMAILS_FROM_EMAIL", default=None)',
        'config("EMAILS_FROM_NAME", default=None)',
        'config("EMAIL_SENDER", default="logger")',
        'config("POSTGRES_POOL_SIZE", default=100)',
        'config("POSTGRES_USER", default="postgres")',
        'config("POSTGRES_PASSWORD", default="postgres")',
        'config("POSTGRES_SERVER", default="127.0.0.1")',
        'config("POSTGRES_PORT", default=5432)',
        'config("POSTGRES_DB", default="postgres")',
        'config("TIER_NAME_DEFAULT", default="Free")',
        'config("USER_SYSTEM_ID", default="94c51c02-01eb-4d72-91d1-4f6c10f08e19")',
        'config("USER_SYSTEM_NAME", default="System User")',
        'config("USER_SYSTEM_EMAIL", default="system@system.com")',
        'config("USER_SYSTEM_USERNAME", default="system")',
        'config("USER_FIRST_ADMIN_ID", default="2f205816-bfe8-41b2-8178-8cfb6b27ba22")',
        'config("USER_FIRST_ADMIN_NAME", default="Admin User")',
        'config("USER_FIRST_ADMIN_EMAIL", default="admin@system.com")',
        'config("USER_FIRST_ADMIN_USERNAME", default="admin")',
        'config("USER_FIRST_ADMIN_PASSWORD", default="!Ch4ng3Th1sP4ssW0rd!")',
        'config("USER_TEST_NAME", default="Tester User")',
        'config("USER_TEST_EMAIL", default="test@tester.com")',
        'config("USER_TEST_USERNAME", default="testeruser")',
        'config("USER_TEST_PASSWORD", default="Str1ng$t")',
        'config("REDIS_CACHE_HOST", default="127.0.0.1")',
        'config("REDIS_CACHE_PORT", default=6379)',
        'config("REDIS_CACHE_DB", default=0)',
        'config("REDIS_CACHE_USERNAME", default="")',
        'config("REDIS_CACHE_PASSWORD", default="nosecurity")',
        'config("REDIS_CACHE_USE_SSL", default=False)',
        'config("REDIS_BROKER_HOST", default="")',
        'config("REDIS_BROKER_PORT", default=6379)',
        'config("REDIS_BROKER_DB", default=0)',
        'config("REDIS_BROKER_USERNAME", default="")',
        'config("REDIS_BROKER_PASSWORD", default="")',
        'config("REDIS_BROKER_USE_SSL", default=False)',
        'config("REDIS_RATE_LIMIT_HOST", default="")',
        'config("REDIS_RATE_LIMIT_PORT", default=6379)',
        'config("REDIS_RATE_LIMIT_DB", default=0)',
        'config("REDIS_RATE_LIMIT_USERNAME", default="")',
        'config("REDIS_RATE_LIMIT_PASSWORD", default="")',
        'config("REDIS_RATE_LIMIT_USE_SSL", default=False)',
        'config("DEFAULT_RATE_LIMIT_LIMIT", default=10)',
        'config("DEFAULT_RATE_LIMIT_PERIOD", default=3600)',
        'config("TRUST_PROXY_HEADERS", default="False")',
        'config("CLIENT_CACHE_MAX_AGE", default=60)',
        'config("CORS_ALLOW_ORIGINS", default="*")',
        'config("CORS_ALLOW_METHODS", default="*")',
        'config("CORS_ALLOW_HEADERS", default="*")',
        'config("CORS_ALLOW_CREDENTIALS", default="False")',
        'config("CORS_EXPOSE_HEADERS", default="")',
        'config("CORS_MAX_AGE", default="600")',
        'config("LOG_FORMAT", default="text")',
        'config("LOG_TO_FILE", default="True")',
        'config("LOG_LEVEL", default="DEBUG")',
        'config("ENVIRONMENT", default="local")',
    }
)


def _env_example_keys() -> set[str]:
    keys: set[str] = set()
    for line in _ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        match = _ENV_EXAMPLE_KEY_RE.match(line.strip())
        if match:
            keys.add(match.group(1))
    return keys


def _redis_cache(**overrides: object) -> RedisCacheSettings:
    data: dict[str, object] = {
        "REDIS_CACHE_HOST": "cache.local",
        "REDIS_CACHE_PORT": 6379,
        "REDIS_CACHE_DB": 0,
        "REDIS_CACHE_USERNAME": "",
        "REDIS_CACHE_PASSWORD": "",
        "REDIS_CACHE_USE_SSL": False,
        "REDIS_CACHE_URL": "redis://placeholder",
    }
    data.update(overrides)
    return RedisCacheSettings.model_validate(data)


def _redis_broker(**overrides: object) -> RedisBrokerSettings:
    data: dict[str, object] = {
        "REDIS_BROKER_HOST": "broker.local",
        "REDIS_BROKER_PORT": 6379,
        "REDIS_BROKER_DB": 0,
        "REDIS_BROKER_USERNAME": "",
        "REDIS_BROKER_PASSWORD": "",
        "REDIS_BROKER_USE_SSL": False,
        "REDIS_BROKER_URL": "redis://placeholder",
    }
    data.update(overrides)
    return RedisBrokerSettings.model_validate(data)


def _redis_rate_limit(**overrides: object) -> RedisRateLimiterSettings:
    data: dict[str, object] = {
        "REDIS_RATE_LIMIT_HOST": "limit.local",
        "REDIS_RATE_LIMIT_PORT": 6379,
        "REDIS_RATE_LIMIT_DB": 0,
        "REDIS_RATE_LIMIT_USERNAME": "",
        "REDIS_RATE_LIMIT_PASSWORD": "",
        "REDIS_RATE_LIMIT_USE_SSL": False,
        "REDIS_RATE_LIMIT_URL": "redis://placeholder",
    }
    data.update(overrides)
    return RedisRateLimiterSettings.model_validate(data)


def test_settings_field_inventory(settings) -> None:
    assert set(type(settings).model_fields) == EXPECTED_SETTINGS_FIELDS


def test_config_source_defaults_match_golden_snippets() -> None:
    source = _CONFIG_PY.read_text(encoding="utf-8")
    keys_in_source = set(_CONFIG_KEY_RE.findall(source))
    snippet_keys: set[str] = set()
    for snippet in EXPECTED_CONFIG_SNIPPETS:
        assert snippet in source, snippet
        snippet_keys.update(_CONFIG_KEY_RE.findall(snippet))

    assert keys_in_source == snippet_keys | KEYS_WITHOUT_STATIC_DEFAULT
    assert 'config("SECRET_KEY")' in source
    assert 'config("USER_SYSTEM_PASSWORD", default=generate_random_password())' in source


def test_env_example_keys_are_settings_fields(settings) -> None:
    unknown = _env_example_keys() - set(type(settings).model_fields) - EXAMPLE_ONLY_KEYS
    assert unknown == set()


def test_redis_cache_url_empty_credentials_includes_db() -> None:
    cache = _redis_cache(REDIS_CACHE_DB=2)
    assert cache.REDIS_CACHE_URL == "redis://cache.local:6379/2"


def test_redis_cache_url_nosecurity_includes_db() -> None:
    cache = _redis_cache(
        REDIS_CACHE_DB=2,
        REDIS_CACHE_USERNAME="cacheuser",
        REDIS_CACHE_PASSWORD="nosecurity",
    )
    assert cache.REDIS_CACHE_URL == "redis://cacheuser@cache.local:6379/2"


def test_redis_cache_url_ssl_with_password_uses_rediss() -> None:
    cache = _redis_cache(
        REDIS_CACHE_DB=4,
        REDIS_CACHE_USERNAME="u",
        REDIS_CACHE_PASSWORD="secret",
        REDIS_CACHE_USE_SSL=True,
        REDIS_CACHE_URL="redis://u:secret@cache.local:6379/4",
    )
    assert cache.REDIS_CACHE_URL == "rediss://u:secret@cache.local:6379/4"


def test_redis_cache_url_ssl_with_empty_credentials_uses_rediss() -> None:
    cache = _redis_cache(REDIS_CACHE_DB=2, REDIS_CACHE_USE_SSL=True)
    assert cache.REDIS_CACHE_URL == "rediss://cache.local:6379/2"


def test_redis_cache_url_ssl_with_nosecurity_uses_rediss() -> None:
    cache = _redis_cache(
        REDIS_CACHE_DB=2,
        REDIS_CACHE_USERNAME="cacheuser",
        REDIS_CACHE_PASSWORD="nosecurity",
        REDIS_CACHE_USE_SSL=True,
    )
    assert cache.REDIS_CACHE_URL == "rediss://cacheuser@cache.local:6379/2"


def test_redis_broker_empty_host_uses_cache_url() -> None:
    broker = _redis_broker(
        REDIS_BROKER_HOST="",
        REDIS_BROKER_DB=9,
        REDIS_BROKER_USERNAME="ignored",
        REDIS_BROKER_PASSWORD="ignored",
    )
    assert broker.REDIS_BROKER_URL == RedisCacheSettings().REDIS_CACHE_URL


def test_redis_broker_explicit_host_uses_broker_db() -> None:
    broker = _redis_broker(REDIS_BROKER_DB=3)
    assert broker.REDIS_BROKER_URL == "redis://broker.local:6379/3"


def test_redis_broker_nosecurity_includes_db() -> None:
    broker = _redis_broker(
        REDIS_BROKER_DB=3,
        REDIS_BROKER_USERNAME="brokeruser",
        REDIS_BROKER_PASSWORD="nosecurity",
    )
    assert broker.REDIS_BROKER_URL == "redis://brokeruser@broker.local:6379/3"


def test_redis_broker_url_ssl_with_password_uses_rediss() -> None:
    broker = _redis_broker(
        REDIS_BROKER_DB=3,
        REDIS_BROKER_USERNAME="u",
        REDIS_BROKER_PASSWORD="secret",
        REDIS_BROKER_USE_SSL=True,
        REDIS_BROKER_URL="redis://u:secret@broker.local:6379/3",
    )
    assert broker.REDIS_BROKER_URL == "rediss://u:secret@broker.local:6379/3"


def test_redis_broker_url_ssl_with_empty_credentials_uses_rediss() -> None:
    broker = _redis_broker(REDIS_BROKER_DB=3, REDIS_BROKER_USE_SSL=True)
    assert broker.REDIS_BROKER_URL == "rediss://broker.local:6379/3"


def test_redis_broker_url_ssl_with_nosecurity_uses_rediss() -> None:
    broker = _redis_broker(
        REDIS_BROKER_DB=3,
        REDIS_BROKER_USERNAME="brokeruser",
        REDIS_BROKER_PASSWORD="nosecurity",
        REDIS_BROKER_USE_SSL=True,
    )
    assert broker.REDIS_BROKER_URL == "rediss://brokeruser@broker.local:6379/3"


def test_redis_rate_limit_empty_host_uses_cache_url() -> None:
    rate_limit = _redis_rate_limit(
        REDIS_RATE_LIMIT_HOST="",
        REDIS_RATE_LIMIT_DB=9,
        REDIS_RATE_LIMIT_USERNAME="ignored",
        REDIS_RATE_LIMIT_PASSWORD="ignored",
    )
    assert rate_limit.REDIS_RATE_LIMIT_URL == RedisCacheSettings().REDIS_CACHE_URL


def test_redis_rate_limit_explicit_host_uses_rate_limit_db() -> None:
    rate_limit = _redis_rate_limit(REDIS_RATE_LIMIT_DB=5)
    assert rate_limit.REDIS_RATE_LIMIT_URL == "redis://limit.local:6379/5"


def test_redis_rate_limit_nosecurity_includes_db() -> None:
    rate_limit = _redis_rate_limit(
        REDIS_RATE_LIMIT_DB=5,
        REDIS_RATE_LIMIT_USERNAME="limituser",
        REDIS_RATE_LIMIT_PASSWORD="nosecurity",
    )
    assert rate_limit.REDIS_RATE_LIMIT_URL == "redis://limituser@limit.local:6379/5"


def test_redis_rate_limit_url_ssl_with_password_uses_rediss() -> None:
    rate_limit = _redis_rate_limit(
        REDIS_RATE_LIMIT_DB=5,
        REDIS_RATE_LIMIT_USERNAME="u",
        REDIS_RATE_LIMIT_PASSWORD="secret",
        REDIS_RATE_LIMIT_USE_SSL=True,
        REDIS_RATE_LIMIT_URL="redis://u:secret@limit.local:6379/5",
    )
    assert rate_limit.REDIS_RATE_LIMIT_URL == "rediss://u:secret@limit.local:6379/5"


def test_redis_rate_limit_url_ssl_with_empty_credentials_uses_rediss() -> None:
    rate_limit = _redis_rate_limit(REDIS_RATE_LIMIT_DB=5, REDIS_RATE_LIMIT_USE_SSL=True)
    assert rate_limit.REDIS_RATE_LIMIT_URL == "rediss://limit.local:6379/5"


def test_redis_rate_limit_url_ssl_with_nosecurity_uses_rediss() -> None:
    rate_limit = _redis_rate_limit(
        REDIS_RATE_LIMIT_DB=5,
        REDIS_RATE_LIMIT_USERNAME="limituser",
        REDIS_RATE_LIMIT_PASSWORD="nosecurity",
        REDIS_RATE_LIMIT_USE_SSL=True,
    )
    assert rate_limit.REDIS_RATE_LIMIT_URL == "rediss://limituser@limit.local:6379/5"


def test_postgres_uris_assembled_when_empty() -> None:
    postgres = PostgresSettings.model_validate(
        {
            "POSTGRES_POOL_SIZE": 100,
            "POSTGRES_USER": "app",
            "POSTGRES_PASSWORD": "secret",
            "POSTGRES_SERVER": "db.local",
            "POSTGRES_PORT": 5432,
            "POSTGRES_DB": "appdb",
            "POSTGRES_ASYNC_URI": "",
            "POSTGRES_CELERY_URI": "",
        }
    )
    async_uri = str(postgres.POSTGRES_ASYNC_URI)
    celery_uri = str(postgres.POSTGRES_CELERY_URI)
    assert async_uri.startswith("postgresql+asyncpg://")
    assert "app:secret@db.local:5432" in async_uri
    assert async_uri.rstrip("/").endswith("appdb")
    assert celery_uri.startswith("db+postgresql://")
    assert "app:secret@db.local:5432" in celery_uri
    assert celery_uri.rstrip("/").endswith("appdb")


def test_log_format_accepts_text_and_json() -> None:
    assert LoggingSettings.model_validate({"LOG_FORMAT": "text"}).LOG_FORMAT == "text"
    assert LoggingSettings.model_validate({"LOG_FORMAT": "json"}).LOG_FORMAT == "json"


def test_log_format_rejects_unknown() -> None:
    with pytest.raises(ValidationError):
        LoggingSettings.model_validate({"LOG_FORMAT": "xml"})


def test_email_sender_falls_back_to_logger_when_smtp_incomplete() -> None:
    email = EmailSettings.model_validate(
        {
            "SMTP_HOST": None,
            "SMTP_PORT": 587,
            "SMTP_USER": None,
            "SMTP_PASSWORD": None,
            "EMAILS_FROM_EMAIL": None,
            "EMAILS_FROM_NAME": None,
            "EMAIL_SENDER": "",
        }
    )
    assert email.EMAIL_SENDER == EmailSenderType.logger


def test_email_sender_smtp_when_credentials_are_set() -> None:
    email = EmailSettings.model_validate(
        {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": 587,
            "SMTP_USER": "user",
            "SMTP_PASSWORD": "pass",
            "EMAILS_FROM_EMAIL": "from@example.com",
            "EMAILS_FROM_NAME": "From",
            "EMAIL_SENDER": "smtp",
        }
    )
    assert email.EMAIL_SENDER == EmailSenderType.smtp
