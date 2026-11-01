from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.auth import require_role
from app.errors import InsufficientPermissions
from app.models import Role, User
from app.security import create_access_token

EMAIL = "user@example.com"
PASSWORD = "test-password"


async def register(client: AsyncClient, email: str = EMAIL, password: str = PASSWORD):
    return await client.post("/auth/register", json={"email": email, "password": password})


async def login(client: AsyncClient, email: str = EMAIL, password: str = PASSWORD):
    return await client.post("/auth/login", data={"username": email, "password": password})


async def test_register_returns_user_without_password(client: AsyncClient) -> None:
    response = await register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == EMAIL
    assert body["role"] == "user"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    await register(client)
    response = await register(client, email="USER@example.com")
    assert response.status_code == 409


async def test_register_short_password_returns_422(client: AsyncClient) -> None:
    response = await register(client, password="short")
    assert response.status_code == 422


async def test_login_returns_working_token(client: AsyncClient) -> None:
    await register(client)

    response = await login(client)
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == EMAIL


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    await register(client)
    response = await login(client, password="wrong-password")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_login_unknown_email_returns_401(client: AsyncClient) -> None:
    response = await login(client, email="nobody@example.com")
    assert response.status_code == 401


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_with_garbage_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401


async def test_me_with_expired_token_returns_401(client: AsyncClient) -> None:
    token = create_access_token(1, "user", expires_delta=timedelta(seconds=-1))
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_me_with_token_of_missing_user_returns_401(client: AsyncClient) -> None:
    token = create_access_token(999, "user")
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_require_role_rejects_wrong_role() -> None:
    checker = require_role(Role.ADMIN)

    with pytest.raises(InsufficientPermissions):
        await checker(User(role=Role.USER))

    admin = User(role=Role.ADMIN)
    assert await checker(admin) is admin
