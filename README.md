# booking-api

[![CI](https://github.com/PreGros/booking-api/actions/workflows/ci.yml/badge.svg)](https://github.com/PreGros/booking-api/actions/workflows/ci.yml)

A booking/reservation REST API. Double-booking is prevented by PostgreSQL itself, not by application code.

**Stack:** FastAPI, SQLAlchemy 2.x (async, asyncpg), PostgreSQL 16, Redis 7, Alembic, pytest + httpx, ruff, uv, Docker.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/resources` | Create a resource |
| GET | `/resources` | List resources |
| GET | `/resources/{id}/availability?start=&end=` | Busy intervals of a resource in a time window (cached) |
| POST | `/bookings` | Create a booking |
| GET | `/bookings` | List bookings |
| DELETE | `/bookings/{id}` | Cancel a booking |

Interactive docs are available at `/docs` when the app is running.

## Caching

The availability endpoint uses cache-aside with Redis: one hash per resource (`availability:{id}`), one field per requested time window. Creating or cancelling a booking deletes the resource's hash, so the next read goes to PostgreSQL.

## Rate limiting

All `/resources` and `/bookings` routes use a fixed-window counter in Redis, per client IP, route and HTTP method. When the limit is exceeded the API returns `429` with a `Retry-After` header. `/health` is not limited.

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

Needs PostgreSQL and Redis from `docker compose up -d` (PostgreSQL also creates the `booking_test` database; tests use Redis database 1 via `TEST_REDIS_URL`).

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