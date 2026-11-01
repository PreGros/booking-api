from httpx import AsyncClient

from tests.test_bookings import payload

WIDE = {"start": "2000-01-01T00:00:00Z", "end": "2100-01-01T00:00:00Z"}


async def make_resource(client: AsyncClient) -> int:
    response = await client.post("/resources", json={"name": "Room A"})
    return response.json()["id"]


async def test_confirmed_booking_is_busy(client: AsyncClient) -> None:
    rid = await make_resource(client)
    await client.post("/bookings", json=payload(rid, "10:00", "11:00"))

    response = await client.get(f"/resources/{rid}/availability", params=WIDE)

    assert response.status_code == 200
    assert len(response.json()["busy"]) == 1


async def test_cancelled_booking_is_not_busy(client: AsyncClient) -> None:
    rid = await make_resource(client)
    created = await client.post("/bookings", json=payload(rid, "10:00", "11:00"))
    await client.delete(f"/bookings/{created.json()['id']}")

    response = await client.get(f"/resources/{rid}/availability", params=WIDE)

    assert response.json()["busy"] == []


async def test_availability_unknown_resource_returns_404(client: AsyncClient) -> None:
    response = await client.get("/resources/999/availability", params=WIDE)
    assert response.status_code == 404