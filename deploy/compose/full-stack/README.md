# Deploy — Docker Compose (Full Stack)

Use this when you want to deploy the entire stack on a single server using Docker Compose.

By default, this stack starts the main production services:

- PostgreSQL
- Redis
- FastAPI API
- Caddy reverse proxy

Migrations, background workers, scheduler and Flower are available through Docker Compose `profiles` and do not start automatically.

## What's included

| Service         | Description                                | Starts by default            |
| --------------- | ------------------------------------------ | ---------------------------- |
| `postgres`      | pgvector/pgvector PostgreSQL service       | Yes                          |
| `redis`         | Redis Alpine service                       | Yes                          |
| `api`           | FastAPI via Uvicorn, behind Caddy          | Yes                          |
| `caddy`         | Reverse proxy with automatic HTTPS support | Yes                          |
| `migrate`       | Runs `alembic upgrade head`                | No — profile `migrate`       |
| `celery_worker` | Celery Worker                              | No — profile `worker`        |
| `celery_beat`   | Celery Beat scheduler                      | No — profile `scheduler`     |
| `celery_flower` | Flower monitoring UI                       | No — profile `observability` |

## Requirements

1. Docker and Docker Compose installed on the server.
2. A `.env` file configured in `backend/.env`. See `backend/.env.example`.
3. Your server IP mapped to your domain through a DNS `A` record.
4. Ports `80` and `443` open on the server firewall.

## Environment setup

This setup uses the existing `backend/.env` file. You do not need to create an extra `.env` file for this Compose stack.

Make sure the required variables are configured, especially:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `REDIS_CACHE_PASSWORD`

If you want to run Flower, also configure:

- `FLOWER_BASIC_AUTH=user:password`

`REDIS_CACHE_PASSWORD` is used as the main Redis password for the Redis container and is also reused by the application for the internal Redis connections configured in this Compose file.

## Caddy configuration

Caddy is used as the reverse proxy for the API.

To enable automatic HTTPS, edit:

```text
deploy/compose/full-stack/Caddyfile
```

and configure your real domain, for example:

```text
api.example.com
```

Your domain must point to the server IP, and ports `80` and `443` must be reachable from the internet.

## How to run

Run all commands from the repository root.

### Start the main production stack

Starts PostgreSQL, Redis, API and Caddy:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  up -d
```

### Run migrations

Usually required before using the API with a fresh database or after deploying code with new Alembic revisions:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile migrate \
  run --rm migrate
```

### Start Celery Worker

Use this when you need to process background jobs:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile worker \
  up -d celery_worker
```

### Stop Celery Worker

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  stop celery_worker
```

### Start Celery Beat

Use this when you need scheduled tasks:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile scheduler \
  up -d celery_beat
```

### Start Flower

Use this when you want to inspect Celery workers and tasks through the Flower UI:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile observability \
  up -d celery_flower
```

### Start all optional services

Starts Celery Worker, Celery Beat and Flower:

```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter-prod \
  --profile worker \
  --profile scheduler \
  --profile observability \
  up -d
```

## Architecture notes

- **Standalone mode**: this Compose file is intended for a single-server deployment where PostgreSQL, Redis, API and reverse proxy run on the same host.
- **Caddy proxy**: Caddy acts as the public entrypoint and can provision Let's Encrypt certificates automatically when configured with a real domain.
- **Internal services**: PostgreSQL, Redis, API and Flower use `expose`, not public `ports`, so they are only reachable inside the Docker network. Caddy is the only public HTTP/HTTPS entrypoint.
- **Security**: PostgreSQL and Redis are not exposed directly to the host network.
- **Resilience**: the `api` container starts only after `postgres` and `redis` pass their healthchecks.
- **Migrations**: migrations do not run automatically. Run the `migrate` profile explicitly when needed.
- **Profiles**: background tasks, scheduler, Flower and migrations do not start by default. Use `--profile` flags to start them.
- **Resources**: the Celery Worker is configured with conservative concurrency to be friendly to small VPS environments.
