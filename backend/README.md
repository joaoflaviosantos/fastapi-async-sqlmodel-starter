# Backend - Manual Instructions

After completing the requirements outlined in the **📋 Prerequisites** section of the main [README.md](../README.md), proceed with the following steps.

> For a higher-level overview of all development modes (Docker, infra-only, native), see the [Development Guide](../docs/development-guide.md).
> For deployment options, see the [Deployment Guide](../docs/deploy-guide.md).
> For the opt-in Redis rate limiter and `TRUST_PROXY_HEADERS`, see the [Rate Limit Guide](../docs/rate-limit-guide.md).
> From the repository root, `python setup.py` is the project CLI (local run, Alembic/tests/Black/mypy, Locust). Deploy stays in the Deployment Guide.

## 🛠️ Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/joaoflaviosantos/fastapi-async-sqlmodel-starter.git
   ```

2. Navigate to the project directory:

   ```bash
   cd fastapi-async-sqlmodel-starter/backend
   ```

3. Install dependencies using Poetry:

   ```bash
   poetry install
   ```

4. Define environment variables in ".env":
   - Copy the ".env.example" file as ".env":

     ```bash
     cp .env.example .env
     ```

   - Open the ".env" file and modify the environment variables accordingly.

     **Note:** Make sure to set a secure and unique value for the `SECRET_KEY`.

     You can generate a secure secret key using the following command:

     ```bash
     poetry run python -c "from fastapi import FastAPI; import secrets; print(secrets.token_urlsafe(32))"
     ```

## 🔀 Database Migration

To create tables in the database, run Alembic migrations:

```bash
poetry run alembic revision --autogenerate
```

And to apply the migration:

```bash
poetry run alembic upgrade head
```

For detailed instructions on database migration using Alembic, refer to the [Database Migrations Guide](../docs/database-migration-guide.md) in the project's documentation.

## 🚀 Running the Backend

Start the FastAPI application:

```bash
poetry run uvicorn src.main:app --reload
```

For more details on running the backend with Uvicorn, consult the [Uvicorn Guide](../docs/uvicorn-guide.md) in the project's documentation.

Start the Celery worker:

**Linux / macOS:**

```bash
poetry run celery -A src.worker:app worker --loglevel=info
```

**Windows** (requires thread pool to prevent asyncio event loop deadlocks):

```bash
poetry run celery -A src.worker:app worker --loglevel=info -P threads
```

Start the Celery Beat scheduler (for periodic tasks):

```bash
poetry run celery -A src.worker:app beat --loglevel=info
```

Or run both worker and beat together (development only):

**Linux / macOS:**

```bash
poetry run celery -A src.worker:app worker --beat --loglevel=info
```

**Windows:**

```bash
poetry run celery -A src.worker:app worker --beat --loglevel=info -P threads
```

For more details on running the Celery worker, refer to the [Celery Guide](../docs/celery-guide.md) in the project's documentation.

## 🧪 Running Tests

Run tests using pytest (from `backend/`):

```bash
poetry run pytest -v
poetry run pytest -m unit -v
poetry run pytest -m integration -v
poetry run pytest -v --cov --cov-report=term-missing --cov-fail-under=80
poetry run mypy src
poetry run ruff format --check .
poetry run ruff check src
```

From the repository root, the same checks are available via `python setup.py tools`.

Pre-commit runs `pytest -m unit` (no Docker, no coverage). Integration tests and the coverage gate need Docker Desktop/Engine running. GitHub Actions job `checks` runs Ruff format, Ruff lint, mypy, and unit tests; job `test` runs the full suite with `--cov-fail-under=80`.

For detailed guidance on running tests and confirming the application's behavior, refer to the [Testing Guide](../docs/testing-guide.md) in the project's documentation.

## 🚧 Pre-Commit

Install once (`cd backend && poetry install && poetry run pre-commit install`). After that, `git commit` runs Ruff format, Ruff lint, and `pytest -m unit` (no Docker, no coverage, no mypy).

Setup, Windows notes, and how this differs from CI: [Pre-Commit Guide](../docs/pre-commit-instructions.md).
