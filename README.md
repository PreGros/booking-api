# booking-api

[![CI](https://github.com/PreGros/booking-api/actions/workflows/ci.yml/badge.svg)](https://github.com/PreGros/booking-api/actions/workflows/ci.yml)

A booking/reservation REST API. Double-booking is prevented by PostgreSQL itself, not by application code.

**Stack:** FastAPI, SQLAlchemy 2.x (async, asyncpg), PostgreSQL 16, Alembic, pytest + httpx, ruff, uv, Docker.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/resources` | Create a resource |
| GET | `/resources` | List resources |
| POST | `/bookings` | Create a booking (`404` unknown resource, `409` overlap) |
| GET | `/bookings` | List bookings |
| DELETE | `/bookings/{id}` | Cancel a booking |

Interactive docs are available at `/docs` when the app is running.

## Run locally

Requires Docker, [uv](https://docs.astral.sh/uv/) and Python 3.13.

```bash
git clone https://github.com/PreGros/booking-api.git
cd booking-api
cp .env.example .env
docker compose up -d          # PostgreSQL + Redis
uv sync
uv run alembic upgrade head   # creates tables, btree_gist extension, constraint
uv run uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs.

## Tests and linting

Needs the database from `docker compose up -d` (it also creates the `booking_test` database).

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

## Docker image

```bash
docker build -t booking-api .
```

The image runs as a non-root user and reads its configuration from environment variables (`DATABASE_URL`, `REDIS_URL`).