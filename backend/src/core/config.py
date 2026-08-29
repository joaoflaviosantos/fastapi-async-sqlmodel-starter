# Built-in Dependencies
from typing import Any, List
from enum import Enum
import os

# Third-Party Dependencies
from pydantic_core.core_schema import ValidationInfo
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings
from starlette.config import Config

# Local Dependencies
from src.core.utils.string import generate_random_password
from src.core.common.enums import EmailSenderType

# Environment Variables Config Getters
current_file_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.abspath(os.path.join(current_file_dir, "..", "..", ".env"))
config = Config(env_path)


class AppSettings(BaseSettings):
    PROJECT_NAME: str = config("PROJECT_NAME", default="FastAPI Async SQLModel Starter")
    PROJECT_DESCRIPTION: str | None = config("PROJECT_DESCRIPTION", default=None)
    APP_VERSION: str | None = config("APP_VERSION", default="0.0.1")
    LICENSE_NAME: str | None = config("LICENSE_NAME", default=None)
    CONTACT_NAME: str | None = config("CONTACT_NAME", default=None)
    CONTACT_EMAIL: str | None = config("CONTACT_EMAIL", default=None)


class WebServerSettings(BaseSettings):
    API_BASE_URL: str = config("API_BASE_URL", default="http://127.0.0.1:8000")
    WEB_CONCURRENCY: int = config("WEB_CONCURRENCY", default=1)  # Number of worker processes for handling requests # fmt: skip


class CryptSettings(BaseSettings):
    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7)


class EmailSettings(BaseSettings):
    SMTP_HOST: str | None = config("SMTP_HOST", default=None)
    SMTP_PORT: int | None = config("SMTP_PORT", default=587)
    SMTP_USER: str | None = config("SMTP_USER", default=None)
    SMTP_PASSWORD: str | None = config("SMTP_PASSWORD", default=None)
    EMAILS_FROM_EMAIL: str | None = config("EMAILS_FROM_EMAIL", default=None)
    EMAILS_FROM_NAME: str | None = config("EMAILS_FROM_NAME", default=None)
    EMAIL_SENDER: EmailSenderType | str = config("EMAIL_SENDER", default="logger")

    @field_validator(
        "SMTP_HOST",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "EMAILS_FROM_EMAIL",
        "EMAILS_FROM_NAME",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        """Convert empty strings to None for optional fields."""
        if v == "":
            return None
        return v

    @field_validator("SMTP_PORT", mode="before")
    @classmethod
    def empty_str_to_default_port(cls, v: str | int | None) -> int:
        """Convert empty strings to default port 587."""
        if v == "" or v is None:
            return 587
        return int(v)

    @field_validator("EMAIL_SENDER", mode="after")
    def assemble_email_sender(cls, v: str | None, info: ValidationInfo) -> Any:
        # Se o usuário explicitamente definiu "logger", usar logger
        if v == EmailSenderType.logger or v == "logger":
            return EmailSenderType.logger

        # Se o usuário quer smtp, verificar se as credenciais estão configuradas
        if isinstance(v, str) and v != "smtp":
            # Valor vazio ou não reconhecido, verificar credenciais
            if (
                info.data["SMTP_HOST"] is None
                or info.data["SMTP_USER"] is None
                or info.data["SMTP_PASSWORD"] is None
                or info.data["EMAILS_FROM_EMAIL"] is None
                or info.data["EMAILS_FROM_NAME"] is None
            ):
                print(
                    "WARNING: Using logger email sender, because SMTP_HOST, SMTP_USER, SMTP_PASSWORD, EMAILS_FROM_EMAIL, EMAILS_FROM_NAME are not set"
                )
                return EmailSenderType.logger

        return EmailSenderType.smtp


class PostgresSettings(BaseSettings):
    # Variables related to the server instance configuration
    POSTGRES_POOL_SIZE: int = config("POSTGRES_POOL_SIZE", default=100)

    # Variables related to database connection details
    POSTGRES_USER: str = config("POSTGRES_USER", default="postgres")
    POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD", default="postgres")
    POSTGRES_SERVER: str = config("POSTGRES_SERVER", default="127.0.0.1")
    POSTGRES_PORT: int = config("POSTGRES_PORT", default=5432)
    POSTGRES_DB: str = config("POSTGRES_DB", default="postgres")
    POSTGRES_ASYNC_URI: PostgresDsn | str = ""
    POSTGRES_CELERY_URI: str = ""

    @field_validator("POSTGRES_ASYNC_URI", mode="after")
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_SERVER"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["POSTGRES_DB"],
                )
        return v

    @field_validator("POSTGRES_CELERY_URI", mode="after")
    def assemble_celery_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            if v == "":
                postgres_celery_uri = PostgresDsn.build(
                    scheme="postgresql",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_SERVER"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["POSTGRES_DB"],
                )
                return f"db+{str(postgres_celery_uri)}"
        return v


class DefaultTierSettings(BaseSettings):
    TIER_NAME_DEFAULT: str = config("TIER_NAME_DEFAULT", default="Free")


class SystemUserSettings(BaseSettings):
    USER_SYSTEM_ID: str = config("USER_SYSTEM_ID", default="94c51c02-01eb-4d72-91d1-4f6c10f08e19")  # fmt: skip
    USER_SYSTEM_NAME: str = config("USER_SYSTEM_NAME", default="System User")
    USER_SYSTEM_EMAIL: str = config("USER_SYSTEM_EMAIL", default="system@system.com")
    USER_SYSTEM_USERNAME: str = config("USER_SYSTEM_USERNAME", default="system")
    USER_SYSTEM_PASSWORD: str = config("USER_SYSTEM_PASSWORD", default=generate_random_password())  # fmt: skip


class FirstAdminUserSettings(BaseSettings):
    USER_FIRST_ADMIN_ID: str = config("USER_FIRST_ADMIN_ID", default="2f205816-bfe8-41b2-8178-8cfb6b27ba22")  # fmt: skip
    USER_FIRST_ADMIN_NAME: str = config("USER_FIRST_ADMIN_NAME", default="Admin User")  # fmt: skip
    USER_FIRST_ADMIN_EMAIL: str = config("USER_FIRST_ADMIN_EMAIL", default="admin@system.com")  # fmt: skip
    USER_FIRST_ADMIN_USERNAME: str = config("USER_FIRST_ADMIN_USERNAME", default="admin")  # fmt: skip
    USER_FIRST_ADMIN_PASSWORD: str = config("USER_FIRST_ADMIN_PASSWORD", default="!Ch4ng3Th1sP4ssW0rd!")  # fmt: skip


class TestSettings(BaseSettings):
    USER_TEST_NAME: str = config("USER_TEST_NAME", default="Tester User")
    USER_TEST_EMAIL: str = config("USER_TEST_EMAIL", default="test@tester.com")
    USER_TEST_USERNAME: str = config("USER_TEST_USERNAME", default="testeruser")
    USER_TEST_PASSWORD: str = config("USER_TEST_PASSWORD", default="Str1ng$t")


class RedisCacheSettings(BaseSettings):
    REDIS_CACHE_HOST: str = config("REDIS_CACHE_HOST", default="127.0.0.1")
    REDIS_CACHE_PORT: int = config("REDIS_CACHE_PORT", default=6379)
    REDIS_CACHE_DB: int = config("REDIS_CACHE_DB", default=0)
    REDIS_CACHE_USERNAME: str = config("REDIS_CACHE_USERNAME", default="")
    REDIS_CACHE_PASSWORD: str = config("REDIS_CACHE_PASSWORD", default="nosecurity")
    REDIS_CACHE_USE_SSL: bool = config("REDIS_CACHE_USE_SSL", default=False)
    REDIS_CACHE_URL: str = f"redis://{REDIS_CACHE_USERNAME}:{REDIS_CACHE_PASSWORD}@{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}/{REDIS_CACHE_DB}"

    @field_validator("REDIS_CACHE_URL", mode="after")
    def assemble_redis_cache_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            # If username and password are not set, use Redis URL connection string without security credentials
            if info.data["REDIS_CACHE_USERNAME"] == "" and info.data["REDIS_CACHE_PASSWORD"] == "":
                v = f"redis://{info.data['REDIS_CACHE_HOST']}:{info.data['REDIS_CACHE_PORT']}/{info.data['REDIS_CACHE_DB']}"
            # If username and password are set, but without security, use Redis URL connection string without password
            elif info.data["REDIS_CACHE_PASSWORD"] == "nosecurity":
                v = f"redis://{info.data['REDIS_CACHE_USERNAME']}@{info.data['REDIS_CACHE_HOST']}:{info.data['REDIS_CACHE_PORT']}/{info.data['REDIS_CACHE_DB']}"
            # If SSL is enabled, change the protocol from 'redis://' to 'rediss://' to ensure the connection is encrypted using SSL/TLS.
            if info.data["REDIS_CACHE_USE_SSL"]:
                v = v.replace("redis://", "rediss://")
        return v


class RedisBrokerSettings(BaseSettings):
    REDIS_BROKER_HOST: str = config("REDIS_BROKER_HOST", default="")
    REDIS_BROKER_PORT: int = config("REDIS_BROKER_PORT", default=6379)
    REDIS_BROKER_DB: int = config("REDIS_BROKER_DB", default=0)
    REDIS_BROKER_USERNAME: str = config("REDIS_BROKER_USERNAME", default="")
    REDIS_BROKER_PASSWORD: str = config("REDIS_BROKER_PASSWORD", default="")
    REDIS_BROKER_USE_SSL: bool = config("REDIS_BROKER_USE_SSL", default=False)
    REDIS_BROKER_URL: str = f"redis://{REDIS_BROKER_USERNAME}:{REDIS_BROKER_PASSWORD}@{REDIS_BROKER_HOST}:{REDIS_BROKER_PORT}/{REDIS_BROKER_DB}"

    @field_validator("REDIS_BROKER_URL", mode="after")
    def assemble_redis_broker_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            # If host is not set, use 'REDIS_CACHE_URL' as Redis Broker URL connection string
            if info.data["REDIS_BROKER_HOST"] == "":
                redis_cache_settings = RedisCacheSettings()
                v = redis_cache_settings.REDIS_CACHE_URL
            # If username and password are not set, use Redis URL connection string without security credentials
            elif (
                info.data["REDIS_BROKER_USERNAME"] == ""
                and info.data["REDIS_BROKER_PASSWORD"] == ""
            ):
                v = f"redis://{info.data['REDIS_BROKER_HOST']}:{info.data['REDIS_BROKER_PORT']}/{info.data['REDIS_BROKER_DB']}"
            # If username and password are set, but without security, use Redis URL connection string without password
            elif info.data["REDIS_BROKER_PASSWORD"] == "nosecurity":
                v = f"redis://{info.data['REDIS_BROKER_USERNAME']}@{info.data['REDIS_BROKER_HOST']}:{info.data['REDIS_BROKER_PORT']}/{info.data['REDIS_BROKER_DB']}"
            # If SSL is enabled, change the protocol from 'redis://' to 'rediss://' to ensure the connection is encrypted using SSL/TLS.
            if info.data["REDIS_BROKER_USE_SSL"]:
                v = v.replace("redis://", "rediss://")
        return v


class RedisRateLimiterSettings(BaseSettings):
    REDIS_RATE_LIMIT_HOST: str = config("REDIS_RATE_LIMIT_HOST", default="")
    REDIS_RATE_LIMIT_PORT: int = config("REDIS_RATE_LIMIT_PORT", default=6379)
    REDIS_RATE_LIMIT_DB: int = config("REDIS_RATE_LIMIT_DB", default=0)
    REDIS_RATE_LIMIT_USERNAME: str = config("REDIS_RATE_LIMIT_USERNAME", default="")
    REDIS_RATE_LIMIT_PASSWORD: str = config("REDIS_RATE_LIMIT_PASSWORD", default="")
    REDIS_RATE_LIMIT_USE_SSL: bool = config("REDIS_RATE_LIMIT_USE_SSL", default=False)
    REDIS_RATE_LIMIT_URL: str = f"redis://{REDIS_RATE_LIMIT_USERNAME}:{REDIS_RATE_LIMIT_PASSWORD}@{REDIS_RATE_LIMIT_HOST}:{REDIS_RATE_LIMIT_PORT}/{REDIS_RATE_LIMIT_DB}"

    @field_validator("REDIS_RATE_LIMIT_URL", mode="after")
    def assemble_redis_rate_limit_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            # If host is not set, use 'REDIS_CACHE_URL' as Redis Queue URL connection string
            if info.data["REDIS_RATE_LIMIT_HOST"] == "":
                redis_cache_settings = RedisCacheSettings()
                v = redis_cache_settings.REDIS_CACHE_URL
            # If username and password are not set, use Redis URL connection string without security credentials
            elif (
                info.data["REDIS_RATE_LIMIT_USERNAME"] == ""
                and info.data["REDIS_RATE_LIMIT_PASSWORD"] == ""
            ):
                v = f"redis://{info.data['REDIS_RATE_LIMIT_HOST']}:{info.data['REDIS_RATE_LIMIT_PORT']}/{info.data['REDIS_RATE_LIMIT_DB']}"
            # If username and password are set, but without security, use Redis URL connection string without password
            elif info.data["REDIS_RATE_LIMIT_PASSWORD"] == "nosecurity":
                v = f"redis://{info.data['REDIS_RATE_LIMIT_USERNAME']}@{info.data['REDIS_RATE_LIMIT_HOST']}:{info.data['REDIS_RATE_LIMIT_PORT']}/{info.data['REDIS_RATE_LIMIT_DB']}"
            # If SSL is enabled, change the protocol from 'redis://' to 'rediss://' to ensure the connection is encrypted using SSL/TLS.
            if info.data["REDIS_RATE_LIMIT_USE_SSL"]:
                v = v.replace("redis://", "rediss://")
        return v


class RedisHashSettings(BaseSettings):
    REDIS_HASH_SYSTEM_AUTH_VALID_USERNAMES: str = "system:auth:valid_usernames"


class DefaultRateLimitSettings(BaseSettings):
    DEFAULT_RATE_LIMIT_LIMIT: int = config("DEFAULT_RATE_LIMIT_LIMIT", default=10)
    DEFAULT_RATE_LIMIT_PERIOD: int = config("DEFAULT_RATE_LIMIT_PERIOD", default=3600)
    TRUST_PROXY_HEADERS: bool = str(config("TRUST_PROXY_HEADERS", default="False")).lower() == "true"  # fmt: skip


class ClientSideCacheSettings(BaseSettings):
    CLIENT_CACHE_MAX_AGE: int = config("CLIENT_CACHE_MAX_AGE", default=60)


class CORSSettings(BaseSettings):
    CORS_ALLOW_ORIGINS: List[str] | str = config("CORS_ALLOW_ORIGINS", default="*").split(",")
    CORS_ALLOW_METHODS: List[str] | str = config("CORS_ALLOW_METHODS", default="*").upper().split(",")  # fmt: skip
    CORS_ALLOW_HEADERS: List[str] | str = config("CORS_ALLOW_HEADERS", default="*").split(",")
    CORS_ALLOW_CREDENTIALS: bool = config("CORS_ALLOW_CREDENTIALS", default="False").lower() == "true"  # fmt: skip
    CORS_EXPOSE_HEADERS: List[str] | str = config("CORS_EXPOSE_HEADERS", default="").split(",")
    CORS_MAX_AGE: int = int(config("CORS_MAX_AGE", default="600"))


class LoggingSettings(BaseSettings):
    LOG_FORMAT: str = str(config("LOG_FORMAT", default="text")).lower()
    LOG_TO_FILE: bool = str(config("LOG_TO_FILE", default="True")).lower() == "true"
    LOG_LEVEL: str = str(config("LOG_LEVEL", default="DEBUG")).upper()

    @field_validator("LOG_FORMAT", mode="after")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        if v not in {"text", "json"}:
            raise ValueError("LOG_FORMAT must be 'text' or 'json'")
        return v


class EnvironmentOption(Enum):
    MIGRATION = "migration"
    TEST = "test"
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = config("ENVIRONMENT", default="local")


class Settings(
    AppSettings,
    WebServerSettings,
    CryptSettings,
    EmailSettings,
    PostgresSettings,
    DefaultTierSettings,
    SystemUserSettings,
    FirstAdminUserSettings,
    TestSettings,
    RedisCacheSettings,
    ClientSideCacheSettings,
    CORSSettings,
    RedisBrokerSettings,
    RedisRateLimiterSettings,
    RedisHashSettings,
    DefaultRateLimitSettings,
    LoggingSettings,
    EnvironmentSettings,
):
    pass


settings = Settings()
