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


async def test_same_slot_on_different_resources_is_allowed(client: AsyncClient) -> None:
    a = await make_resource(client, "Room A")
    b = await make_resource(client, "Room B")
    await client.post("/bookings", json=payload(a, "10:00", "11:00"))
    response = await client.post("/bookings", json=payload(b, "10:00", "11:00"))
    assert response.status_code == 201


async def test_end_before_start_returns_422(client: AsyncClient) -> None:
    rid = await make_resource(client)
    response = await client.post("/bookings", json=payload(rid, "11:00", "10:00"))
    assert response.status_code == 422


async def test_naive_datetime_returns_422(client: AsyncClient) -> None:
    rid = await make_resource(client)
    body = payload(rid, "10:00", "11:00")
    body["start"] = "2026-11-01T10:00:00"  # no timezone
    response = await client.post("/bookings", json=body)
    assert response.status_code == 422


async def test_unknown_resource_returns_404(client: AsyncClient) -> None:
    response = await client.post("/bookings", json=payload(999, "10:00", "11:00"))
    assert response.status_code == 404


async def test_cancelled_booking_frees_the_slot(client: AsyncClient) -> None:
    rid = await make_resource(client)
    first = await client.post("/bookings", json=payload(rid, "10:00", "11:00"))
    cancel = await client.delete(f"/bookings/{first.json()['id']}")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    again = await client.post("/bookings", json=payload(rid, "10:00", "11:00", "b@x.com"))
    assert again.status_code == 201


async def test_concurrent_bookings_only_one_wins(client: AsyncClient) -> None:
    rid = await make_resource(client)

    responses = await asyncio.gather(
        *(
            client.post("/bookings", json=payload(rid, "10:00", "11:00", f"user{i}@x.com"))
            for i in range(20)
        )
    )

    codes = [r.status_code for r in responses]
    assert codes.count(201) == 1
    assert codes.count(409) == 19
