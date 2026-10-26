import asyncio

from httpx import AsyncClient


def payload(resource_id: int, start: str, end: str, email: str = "a@x.com") -> dict:
    return {
        "resource_id": resource_id,
        "customer_email": email,
        "start": f"2026-11-01T{start}:00Z",
        "end": f"2026-11-01T{end}:00Z",
    }


async def make_resource(client: AsyncClient, name: str = "Room A") -> int:
    response = await client.post("/resources", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


async def test_create_resource_duplicate_name_returns_409(client: AsyncClient) -> None:
    await make_resource(client)
    response = await client.post("/resources", json={"name": "Room A"})
    assert response.status_code == 409


async def test_create_booking(client: AsyncClient) -> None:
    rid = await make_resource(client)
    response = await client.post("/bookings", json=payload(rid, "10:00", "11:00"))
    assert response.status_code == 201
    assert response.json()["status"] == "confirmed"


async def test_overlapping_booking_returns_409(client: AsyncClient) -> None:
    rid = await make_resource(client)
    await client.post("/bookings", json=payload(rid, "10:00", "11:00"))
    response = await client.post("/bookings", json=payload(rid, "10:30", "11:30"))
    assert response.status_code == 409


async def test_back_to_back_bookings_are_allowed(client: AsyncClient) -> None:
    rid = await make_resource(client)
    await client.post("/bookings", json=payload(rid, "10:00", "11:00"))
    response = await client.post("/bookings", json=payload(rid, "11:00", "12:00"))
    assert response.status_code == 201