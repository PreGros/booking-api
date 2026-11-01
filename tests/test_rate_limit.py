from httpx import AsyncClient

from app.config import settings
from tests.test_bookings import payload


async def test_rate_limit_returns_429(admin_client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_requests", 3)

    for _ in range(3):
        response = await admin_client.post("/bookings", json=payload(999, "10:00", "11:00"))
        assert response.status_code == 404

    response = await admin_client.post("/bookings", json=payload(999, "10:00", "11:00"))

    assert response.status_code == 429
    assert "retry-after" in response.headers


async def test_rate_limit_ignores_path_params(admin_client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_requests", 3)

    # Different ids, same route: must share one counter
    for booking_id in (1, 2, 3):
        response = await admin_client.delete(f"/bookings/{booking_id}")
        assert response.status_code == 404  # allowed through, booking doesn't exist

    response = await admin_client.delete("/bookings/4")

    assert response.status_code == 429


async def test_rate_limit_is_per_method(admin_client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_requests", 2)

    # Use up the GET /bookings limit
    for _ in range(2):
        assert (await admin_client.get("/bookings")).status_code == 200
    assert (await admin_client.get("/bookings")).status_code == 429

    # POST /bookings has its own counter and is still allowed
    response = await admin_client.post("/bookings", json=payload(999, "10:00", "11:00"))

    assert response.status_code == 404
