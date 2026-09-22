<h1 align="center">FastAPI Async SQLModel Starter</h1>

<p align="center" markdown=1>
  <i>Supercharge your FastAPI development. A backend for perfectionists with deadlines and lovers of asynchronous programming.</i>
</p>

<p align="center">
  <a href="https://github.com/joaoflaviosantos/fastapi-async-sqlmodel-starter">
    <img src="https://github-production-user-asset-6210df.s3.amazonaws.com/80658056/293617785-78ad080b-2416-473a-91cd-0adc33acf027.png" alt="White and blue rocket with FastAPI text on it. A Python logo floating next to the rocket." width="35%" height="auto">
  </a>
</p>

<p align="center">
  <a href="https://www.python.org">
      <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://fastapi.tiangolo.com">
      <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  </a>
  <a href="https://sqlmodel.tiangolo.com">
      <img src="https://img.shields.io/badge/SQLModel-7E56C2?style=for-the-badge&logo=sqlmodel&logoColor=fff" alt="SQLModel">
  </a>
  <a href="https://docs.pydantic.dev/2.4/">
      <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=fff&style=for-the-badge" alt="Pydantic">
  </a>
  <a href="https://docs.sqlalchemy.org/en/20/">
      <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=fff" alt="SQLAlchemy">
  </a>
  <a href="https://www.postgresql.org">
      <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  </a>
  <a href="https://redis.io">
      <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=fff&style=for-the-badge" alt="Redis">
  </a>
  <a href="https://docs.docker.com/compose/">
      <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff&style=for-the-badge" alt="Docker">
  </a>
  <a href="https://deepwiki.com/joaoflaviosantos/fastapi-async-sqlmodel-starter">
      <img src="https://img.shields.io/badge/DeepWiki-1F2937?logo=deepwiki&logoColor=white&style=for-the-badge" alt="DeepWiki">
  </a>
</p>

<p align="center">
  <a href="https://github.com/joaoflaviosantos/fastapi-async-sqlmodel-starter/actions/workflows/tests.yml">
      <img src="https://github.com/joaoflaviosantos/fastapi-async-sqlmodel-starter/actions/workflows/tests.yml/badge.svg" alt="Tests">
  </a>
</p>

## 🔍 Project Overview

A production-ready **FastAPI** starter — fully async, with **SQLModel**, **Redis**, **Celery**, and **Docker**. It uses a Django-inspired folder layout and **Clean Architecture**: routers handle HTTP, services hold business rules, and repositories talk to the database.

Tests live next to each feature and run in GitHub Actions. Deploy the way that fits you: Compose, PaaS, or Nginx. An optional **Locust** suite is there for load testing.

It is a **solid foundation** for API work and a fast path to a **POC** or **MVP** — especially if you like how Django is organized but want a clearer split of layers.

## 🌟 Key Features

A **strong foundation for API development**, with a practical stack and a clear structure:

- 🏛️ **Clean Architecture:** Routers handle HTTP, services hold business logic, and repositories manage data access.
- ⚡️ **Fully Async:** The stack is asynchronous end to end.
- 🚀 **FastAPI:** High-performance APIs with automatic OpenAPI docs.
- 🧰 **SQLModel:** One model for the database and the API (SQLAlchemy 2.0 + Pydantic), instead of mapping persistence and transport separately.
- 🔐 **JWT User Authentication:** Secure user authentication with JSON Web Tokens.
- 🍪 **Cookie-based Refresh Token:** Refresh tokens stored in cookies.
- 🏬 **Easy Redis Caching:** Simple, effective caching with Redis.
- 👜 **Client-side Caching:** HTTP caching headers for faster clients.
- 🚦 **Celery:** Async task queues, scheduled jobs (Beat), and a PostgreSQL result backend.
- ⚙️ **Efficient Querying:** Fetch only what you need, including joins.
- ⎘ **Pagination Support:** Built-in pagination for list endpoints.
- 💌 **FastAPI-Mail:** Async email with templates, off the request path when needed.
- 🛑 **Rate Limiter:** Redis-backed limiter for controlled API access.
- 👮 **Secure FastAPI Docs:** Auth-gated docs, hidden outside development.
- 🚚 **Deploy Menu:** Compose full-stack (Caddy HTTPS), app-only (PaaS / managed databases), or native (Nginx + Supervisor).
- 🦗 **Load Testing with Locust:** Optional independent suite for performance and stress tests.
- 🧪 **Tests next to the code:** HTTP and service tests live with each feature. Unit tests run without Docker; the full suite (and a coverage gate) runs in CI.
- ✅ **CI:** GitHub Actions checks format, types, and tests on every push.
- 🦾 **Easy to extend:** Add your own apps without fighting the layout.

## 🎯 Project Goals

- [x] FastAPI for high-performance APIs.
- [x] Async programming throughout.
- [x] Redis for caching, rate limiting, and faster data access.
- [x] Celery for background work, with async tasks.
- [x] A solid logging setup.
- [x] Database migrations with Alembic.
- [x] Async HTTP tests against isolated PostgreSQL and Redis.
- [x] Isolated service unit tests (no live database).
- [x] CI with a coverage gate, type checks, and formatting on every push.
- [x] SQLModel so the database and the API share one model.
- [x] Repository and Service patterns for a clear split of concerns.
- [x] `AGENTS.md` and first-party skills so coding agents follow the same app layout.
- [x] Docker Compose for local PostgreSQL and Redis.
- [x] Deploy options: Compose full-stack (Caddy), app-only (PaaS), and native (Nginx + Supervisor).
- [x] Local development on both **Linux** and **Windows**.
- [x] A CLI (`python setup.py`) to run and manage the project.

## 📋 Prerequisites

Before you begin, ensure you have the following:

- [Python](https://www.python.org) 3.11 or newer.
- [Poetry](https://python-poetry.org) **1.7.1** for dependency management.
- [Docker](https://www.docker.com) (Engine or Desktop): used for Compose (infra-only / full-stack) and for Testcontainers when you run the full pytest suite.

PostgreSQL and Redis on the host are **optional**. Prefer Compose infra-only (or the CLI below) unless you explicitly want a native database install.

### Installing Poetry

Poetry is a dependency manager for Python. Follow the steps below to install Poetry **version 1.7.1** (required):

1. Open a terminal.
2. `pip install poetry==1.7.1`
3. `poetry --version` must print `Poetry (version 1.7.1)`.
4. If the version is anything else:

```bash
pip uninstall poetry
pip install poetry==1.7.1
```

To refresh `backend/poetry.lock` on this version (does not bump resolved packages):

```bash
cd backend
poetry lock --no-update
```

Do not run `poetry lock` without `--no-update` (Poetry 1.7.1 resolves/updates dependencies). Native helper scripts live under `development/native/scripts/` — see the [Development Guide](docs/development-guide.md).

### Using Docker Compose (recommended for databases)

From the **root directory**, start PostgreSQL and Redis:

```bash
docker compose --env-file backend/.env -f development/compose/infra-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-starter up -d
```

```bash
docker compose --project-name fastapi-async-sqlmodel-starter ps
docker compose --project-name fastapi-async-sqlmodel-starter down
```

The command uses environment variables from `backend/.env`. Copy `backend/.env.example` first if needed (local defaults use `127.0.0.1`).

For full-stack Docker, native host, or other modes, see the [Development Guide](docs/development-guide.md).

## 🤖 Running the Project CLI

From the **repository root**:

```bash
python3 setup.py
```

Or jump to a submenu: `python setup.py local`, `python setup.py tools`, `python setup.py locust`. `python setup.py --help` lists the commands.

| Option                        | What it does                                                                                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1 – Local Development**     | Copies `.env.example` if needed, generates `SECRET_KEY`, starts FastAPI / Celery / Flower. Setup wizard appears only when `backend/.env` is missing required values (ENTER keeps defaults). |
| **2 – Project Tools**         | Alembic (`upgrade`, `revision --autogenerate`, `current`), pytest (unit / integration / full / coverage), Ruff, mypy, and a CI-checks shortcut.                                             |
| **3 – Load Testing (Locust)** | Installs the independent Locust env and starts the Web UI or a headless run.                                                                                                                |
| **4 – Exit**                  | Leave the CLI.                                                                                                                                                                              |

Production deploy is **not** in this menu — use the [Deployment Guide](docs/deploy-guide.md).

For a manual setup, see the [Backend README](backend/README.md). For load testing details, see the [Locust Guide](docs/locust-guide.md).

## 🧪 Running Tests

From `backend/`:

```bash
cd backend
poetry run pytest -m unit -v
poetry run pytest -v --cov --cov-report=term-missing --cov-fail-under=80
poetry run mypy src
```

`pytest -m unit` needs no Docker (pre-commit and GitHub Actions job `checks`). The full suite and the 80% coverage gate need Docker so Testcontainers can start PostgreSQL and Redis.

From the repository root you can run the same commands via **Project Tools**: `python setup.py tools`.

Details: [Testing Guide](docs/testing-guide.md).

## 📚 Documentation

| Guide                                                        | Description                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------------- |
| [Coding Agents](docs/ai-coding-guide.md)                     | `AGENTS.md` and first-party skills for this backend                 |
| [Development Guide](docs/development-guide.md)               | All local development modes (Docker, native, infra-only)            |
| [Deployment Guide](docs/deploy-guide.md)                     | Production modes: Caddy (Compose full-stack), PaaS, or Nginx native |
| [Database Migration Guide](docs/database-migration-guide.md) | Alembic workflow for schema changes                                 |
| [Celery Guide](docs/celery-guide.md)                         | Celery worker setup and Windows-specific notes                      |
| [Testing Guide](docs/testing-guide.md)                       | Unit tests, HTTP tests, coverage gate, mypy, and CI                 |
| [Rate Limit Guide](docs/rate-limit-guide.md)                 | Opt-in Redis limiter, path matching, and `TRUST_PROXY_HEADERS`      |
| [Uvicorn Guide](docs/uvicorn-guide.md)                       | Local Uvicorn, Compose, and native Gunicorn workers                 |
| [Locust Guide](docs/locust-guide.md)                         | Optional load testing with Locust                                   |

## 🌐 Reference Projects

- [FastAPI Boilerplate by Igor Magalhães](https://github.com/igorbenav/FastAPI-boilerplate)
- [FastAPI Alembic SQLModel Async by Jonathan Vargas](https://github.com/jonra1993/fastapi-alembic-sqlmodel-async)
- [FastAPI do zero by Dunossauro](https://github.com/dunossauro/fastapi-do-zero)

## Source available

This repository is a **personal starter** shared as a gift. Clone it, fork it, or copy it into **your** project and adapt it there — that is what the [MIT license](LICENSE) is for.

It is not a community project. I am not looking for pull requests, feature requests, or a contributor community. If you want to change something, do it in your own copy. Happy coding! 🌟
