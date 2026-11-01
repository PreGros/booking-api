from httpx import AsyncClient

from app.config import settings
from tests.test_bookings import payload


async def test_rate_limit_returns_429(client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_requests", 3)

    for _ in range(3):
        response = await client.post("/bookings", json=payload(999, "10:00", "11:00"))
        assert response.status_code == 404

    response = await client.post("/bookings", json=payload(999, "10:00", "11:00"))

    assert response.status_code == 429
    assert "retry-after" in response.headers
