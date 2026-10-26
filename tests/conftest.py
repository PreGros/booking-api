from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.config import settings
from app.db import get_session
from app.main import app
from app.models import Base


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
async def client(db_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    # Dependency override: the app now talks to the test database
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
