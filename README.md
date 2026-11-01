# booking-api

[![CI](https://github.com/PreGros/booking-api/actions/workflows/ci.yml/badge.svg)](https://github.com/PreGros/booking-api/actions/workflows/ci.yml)

A booking/reservation REST API. Double-booking is prevented by PostgreSQL itself, not by application code.

**Stack:** FastAPI, SQLAlchemy 2.x (async, asyncpg), PostgreSQL 16, Redis 7, Alembic, JWT auth, pytest + httpx, ruff, uv, Docker.

## Endpoints

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/health` | public | Health check |
| POST | `/auth/register` | public | Register a user |
| POST | `/auth/login` | public | Log in, returns a JWT access token |
| GET | `/auth/me` | logged in | Current user |
| POST | `/resources` | admin | Create a resource |
| GET | `/resources` | public | List resources |
| GET | `/resources/{id}/availability?start=&end=` | public | Busy intervals of a resource in a time window (cached) |
| POST | `/bookings` | logged in | Create a booking, linked to the current user |
| GET | `/bookings` | logged in | List bookings (own bookings; admins see all) |
| DELETE | `/bookings/{id}` | owner or admin | Cancel a booking |

Interactive docs are available at `/docs` when the app is running. Use the **Authorize** button there to log in.

## Authentication

- Passwords are hashed with Argon2. Login returns a signed JWT (HS256) that expires after 30 minutes.
- Two roles: `user` (default for new registrations) and `admin`. The role is read from the database on every request, so a role change applies immediately.
- Unknown email and wrong password return the same `401`, so registered emails are not revealed.
- Cancelling someone else's booking returns `404`, so booking ids are not revealed.
- Admins cannot be created through the API. Promote a user (or create one) with a script:

```bash
uv run python -m scripts.create_admin you@example.com
```

## Caching

The availability endpoint uses cache-aside with Redis: one hash per resource (`availability:{id}`), one field per requested time window. Creating or cancelling a booking deletes the resource's hash, so the next read goes to PostgreSQL.

## Rate limiting

All `/auth`, `/resources` and `/bookings` routes use a fixed-window counter in Redis, per client IP, route and HTTP method. When the limit is exceeded the API returns `429` with a `Retry-After` header. `/health` is not limited.

## Run locally

Requires Docker, [uv](https://docs.astral.sh/uv/) and Python 3.13.

```bash
git clone https://github.com/PreGros/booking-api.git
cd booking-api
cp .env.example .env          # then set JWT_SECRET (see below)
docker compose up -d          # PostgreSQL + Redis
uv sync
uv run alembic upgrade head   # creates tables, btree_gist extension, constraint
uv run uvicorn app.main:app --reload
```

Generate a value for `JWT_SECRET` in `.env` with `openssl rand -hex 32`.

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

The image runs as a non-root user and reads its configuration from environment variables (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`).