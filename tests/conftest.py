from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.cache import get_redis
from app.config import settings
from app.db import get_session
from app.main import app
from app.models import Base, Role, User
from app.security import create_access_token


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    assert settings.test_database_url != settings.database_url

    engine = create_async_engine(settings.test_database_url)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def redis_client() -> AsyncIterator[Redis]:
    r = Redis.from_url(settings.test_redis_url, decode_responses=True)
    await r.flushdb()
    yield r
    await r.flushdb()
    await r.aclose()


@pytest.fixture
async def client(
    db_engine: AsyncEngine,
    redis_client: Redis,
) -> AsyncIterator[AsyncClient]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis] = lambda: redis_client

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c

    app.dependency_overrides.clear()


@asynccontextmanager
async def _authed_client(
    db_engine: AsyncEngine,
    email: str,
    role: Role,
) -> AsyncGenerator[AsyncClient]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async with factory() as session:
        user = User(email=email, hashed_password="not-used", role=role)
        session.add(user)
        await session.commit()

    token = create_access_token(user.id, user.role)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c


# Each fixture depends on `client` only so its dependency overrides are installed.
@pytest.fixture
async def admin_client(client: AsyncClient, db_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    async with _authed_client(db_engine, "admin@example.com", Role.ADMIN) as c:
        yield c


@pytest.fixture
async def user_client(client: AsyncClient, db_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    async with _authed_client(db_engine, "user@example.com", Role.USER) as c:
        yield c


@pytest.fixture
async def other_user_client(
    client: AsyncClient, db_engine: AsyncEngine
) -> AsyncIterator[AsyncClient]:
    async with _authed_client(db_engine, "other@example.com", Role.USER) as c:
        yield c
