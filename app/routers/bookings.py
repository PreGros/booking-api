from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth import CurrentUser
from app.cache import RedisDep, availability_key
from app.db import SessionDep
from app.models import Role
from app.ratelimit import rate_limit
from app.schemas import BookingCreate, BookingRead
from app.services import bookings as booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"], dependencies=[Depends(rate_limit)])


@router.post("", status_code=201, response_model=BookingRead)
async def create_booking(
    data: BookingCreate, session: SessionDep, redis: RedisDep, user: CurrentUser
) -> BookingRead:
    booking = await booking_service.create_booking(session, data, user.id)
    await redis.delete(availability_key(booking.resource_id))
    return BookingRead.from_model(booking)


@router.get("", response_model=list[BookingRead])
async def list_bookings(
    session: SessionDep,
    user: CurrentUser,
    resource_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[BookingRead]:
    owner_id = None if user.role == Role.ADMIN else user.id
    bookings = await booking_service.list_bookings(session, resource_id, limit, offset, owner_id)
    return [BookingRead.from_model(b) for b in bookings]


@router.delete("/{booking_id}", response_model=BookingRead)
async def cancel_booking(
    booking_id: int, session: SessionDep, redis: RedisDep, user: CurrentUser
) -> BookingRead:
    booking = await booking_service.cancel_booking(session, booking_id, user)
    await redis.delete(availability_key(booking.resource_id))
    return BookingRead.from_model(booking)
