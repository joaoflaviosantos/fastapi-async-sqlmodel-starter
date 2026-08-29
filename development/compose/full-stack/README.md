# Development — Docker Compose (Full Stack)

Use this when you want to run the local development stack inside Docker with hot-reload enabled.

By default, this stack starts only the main development environment:

- PostgreSQL
- Redis
- FastAPI API with hot reload

Background services, migrations, scheduler and observability tools are available through Docker Compose `profiles`.

## What's included

| Service         | Description                                     | Starts by default            |
| --------------- | ----------------------------------------------- | ---------------------------- |
| `postgres`      | pgvector/pgvector (PostgreSQL 17)               | Yes                          |
| `redis`         | Redis Alpine                                    | Yes                          |
| `api`           | FastAPI via Uvicorn with `--reload` (dev image) | Yes                          |
| `migrate`       | Alembic migration runner                        | No — profile `migrate`       |
| `celery_worker` | Celery Worker                                   | No — profile `worker`        |
| `celery_beat`   | Celery Beat scheduler                           | No — profile `scheduler`     |
| `celery_flower` | Flower monitoring UI                            | No — profile `observability` |

## Requirements

- Docker and Docker Compose installed
- `backend/.env` file configured. See `backend/.env.example`
- `FLOWER_BASIC_AUTH=user:password` set in `backend/.env` only if you want to run Flower

## How to run

Run all commands from the repository root.

### Start the main development environment

Starts PostgreSQL, Redis and the FastAPI API:

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  up -d
```

### Run migrations

Usually required before using the API with a fresh database:

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  --profile migrate \
  run --rm migrate
```

### Start Celery Worker

Use this when you need to process background jobs:

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  --profile worker \
  up -d celery_worker
```

### Start Celery Beat

Use this when you need scheduled tasks:

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  --profile scheduler \
  up -d celery_beat
```

### Start Flower

Use this only when you want to inspect Celery workers and tasks through the Flower UI:

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  --profile observability \
  up -d celery_flower
```

### Start all optional services

Starts Celery Worker, Celery Beat and Flower:

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  --profile worker \
  --profile scheduler \
  --profile observability \
  up -d
```

### Stop Celery Worker

```bash
docker compose --env-file backend/.env \
  -f development/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter \
  stop celery_worker
```

## Notes

- The `backend/` directory is mounted as a volume into all app containers, so code changes are reflected immediately without rebuilding.
- Connection variables such as `POSTGRES_SERVER`, `REDIS_*_HOST` and `REDIS_*_PASSWORD` are overridden automatically inside this Compose file so they point to the Docker service names.
- Host-published ports bind to IPv4 loopback: API `http://127.0.0.1:8000`, Flower `http://127.0.0.1:5555`, Postgres `127.0.0.1:5432`, Redis `127.0.0.1:6379`. Prefer `127.0.0.1` over `localhost` (Windows often resolves `localhost` to IPv6).
- Background tasks, scheduler, Flower and migrations do not start by default. Use `--profile` flags to start them explicitly.
- The Celery Worker may be configured with conservative concurrency, such as `--concurrency=1`, to keep local development lightweight on small machines.
- Flower requires `FLOWER_BASIC_AUTH=user:password` in `backend/.env`.
