# Deploy — Docker Compose (App Only)

Use this when PostgreSQL and Redis are provisioned externally by a platform or managed cloud service.

This Compose file contains only application services:

- FastAPI API
- Alembic migration runner
- Celery Worker
- Celery Beat
- Flower

It does not include PostgreSQL, Redis or a reverse proxy. Those services are expected to be provided externally and reached through environment variables.

## What's included

| Service         | Description                 | Starts by default            |
| --------------- | --------------------------- | ---------------------------- |
| `api`           | FastAPI via Uvicorn         | Yes                          |
| `migrate`       | Runs `alembic upgrade head` | No — profile `migrate`       |
| `celery_worker` | Celery Worker               | No — profile `worker`        |
| `celery_beat`   | Celery Beat scheduler       | No — profile `scheduler`     |
| `celery_flower` | Flower monitoring UI        | No — profile `observability` |

## When to use this mode

Use `app-only` when PostgreSQL, Redis and the reverse proxy are managed outside this Compose file.

Common examples:

- Dokploy, Coolify, CapRover or Portainer with databases created separately
- PostgreSQL from AWS RDS, Azure Database for PostgreSQL, Supabase, Neon, Railway, etc.
- Redis from ElastiCache, Azure Cache for Redis, Upstash, Railway, etc.
- A platform-provided reverse proxy, such as Traefik, Caddy, Nginx or the platform routing layer

For a standalone single-server deployment where PostgreSQL, Redis and Caddy should also run in Docker Compose, use:

```text
deploy/compose/full-stack/docker-compose.yml
```

## Requirements

- Docker and Docker Compose installed, when running manually.
- An external Docker network must already exist.
- `backend/.env` must be configured. See `backend/.env.example`.
- PostgreSQL and Redis must already be running and reachable from the application containers.
- A reverse proxy or platform routing layer must route external traffic to the `api` service.

By default, this Compose file expects an external Docker network named:

```text
app-network
```

If your platform creates a different network, rename `app-network` in the Compose file to match it.

For example, if running manually:

```bash
docker network create app-network
```

## Environment variables

All connection variables must be configured in `backend/.env` or through your platform environment variables UI.

Required database variables usually include:

```text
POSTGRES_SERVER
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
```

Required Redis variables usually include:

```text
REDIS_CACHE_HOST
REDIS_CACHE_PASSWORD
REDIS_RATE_LIMIT_HOST
REDIS_RATE_LIMIT_PASSWORD
REDIS_QUEUE_HOST
REDIS_QUEUE_PASSWORD
REDIS_BROKER_HOST
REDIS_BROKER_PASSWORD
REDIS_PUBSUB_HOST
REDIS_PUBSUB_PASSWORD
```

If you want to run Flower, also configure:

```text
FLOWER_BASIC_AUTH=user:password
```

## How to run

Run all commands from the repository root.

### Start the API

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  up -d api
```

### Run migrations

Usually required before using the API with a fresh database or after deploying code with new Alembic revisions:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile migrate \
  run --rm migrate
```

### Start Celery Worker

Use this when you need to process background jobs:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile worker \
  up -d celery_worker
```

### Stop Celery Worker

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  stop celery_worker
```

### Start Celery Beat

Use this when you need scheduled tasks:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile scheduler \
  up -d celery_beat
```

### Start Flower

Use this when you want to inspect Celery workers and tasks through the Flower UI:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile observability \
  up -d celery_flower
```

### Start all optional services

Starts Celery Worker, Celery Beat and Flower:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile worker \
  --profile scheduler \
  --profile observability \
  up -d
```

## Notes

- This file does not start PostgreSQL, Redis or a reverse proxy.
- The `api` service is the only service that starts by default.
- Migrations do not run automatically. Run the `migrate` profile explicitly when needed.
- Background tasks, scheduler and Flower do not start by default. Use `--profile` flags to start them.
- The `api` container does not wait for migrations automatically.
- Since PostgreSQL and Redis are external, this Compose file does not define healthchecks for them.
- The Celery Worker is configured with conservative concurrency to be friendly to small VPS environments.
- If this file uses `expose`, the platform reverse proxy should route traffic through the Docker network.
- If you are running this manually without a reverse proxy, replace `expose` with explicit `ports`, such as `8000:8000`.
