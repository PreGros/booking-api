from httpx import AsyncClient

from tests.test_availability import WIDE, make_resource
from tests.test_bookings import payload


async def test_anonymous_cannot_create_booking(
    admin_client: AsyncClient, client: AsyncClient
) -> None:
    rid = await make_resource(admin_client)
    response = await client.post("/bookings", json=payload(rid, "10:00", "11:00"))
    assert response.status_code == 401


async def test_anonymous_cannot_create_resource(client: AsyncClient) -> None:
    response = await client.post("/resources", json={"name": "Room A"})
    assert response.status_code == 401


async def test_user_cannot_create_resource(user_client: AsyncClient) -> None:
    response = await user_client.post("/resources", json={"name": "Room A"})
    assert response.status_code == 403


async def test_resources_and_availability_are_public(
    admin_client: AsyncClient, client: AsyncClient
) -> None:
    rid = await make_resource(admin_client)
    assert (await client.get("/resources")).status_code == 200
    assert (await client.get(f"/resources/{rid}/availability", params=WIDE)).status_code == 200


async def test_booking_is_linked_to_creator(
    admin_client: AsyncClient, user_client: AsyncClient
) -> None:
    rid = await make_resource(admin_client)
    me = (await user_client.get("/auth/me")).json()

    response = await user_client.post("/bookings", json=payload(rid, "10:00", "11:00"))

    assert response.status_code == 201
    assert response.json()["user_id"] == me["id"]


async def test_user_lists_only_own_bookings(
    admin_client: AsyncClient, user_client: AsyncClient, other_user_client: AsyncClient
) -> None:
    rid = await make_resource(admin_client)
    await user_client.post("/bookings", json=payload(rid, "10:00", "11:00"))
    await other_user_client.post("/bookings", json=payload(rid, "12:00", "13:00"))

    assert len((await user_client.get("/bookings")).json()) == 1
    assert len((await admin_client.get("/bookings")).json()) == 2


async def test_user_cannot_cancel_foreign_booking(
    admin_client: AsyncClient, user_client: AsyncClient, other_user_client: AsyncClient
) -> None:
    rid = await make_resource(admin_client)
    created = await user_client.post("/bookings", json=payload(rid, "10:00", "11:00"))
    booking_id = created.json()["id"]

    assert (await other_user_client.delete(f"/bookings/{booking_id}")).status_code == 404
    assert (await user_client.delete(f"/bookings/{booking_id}")).status_code == 200


async def test_admin_can_cancel_any_booking(
    admin_client: AsyncClient, user_client: AsyncClient
) -> None:
    rid = await make_resource(admin_client)
    created = await user_client.post("/bookings", json=payload(rid, "10:00", "11:00"))

    response = await admin_client.delete(f"/bookings/{created.json()['id']}")

    assert response.status_code == 200
