from typing import Annotated

from fastapi import APIRouter, Query

from app.db import SessionDep
from app.schemas import BookingCreate, BookingRead
from app.services import bookings as booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=201)
async def create_booking(data: BookingCreate, session: SessionDep) -> BookingRead:
    booking = await booking_service.create_booking(session, data)
    return BookingRead.from_model(booking)


@router.get("", response_model=list[BookingRead])
async def list_bookings(
    session: SessionDep,
    resource_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[BookingRead]:
    bookings = await booking_service.list_bookings(session, resource_id, limit, offset)
    return [BookingRead.from_model(b) for b in bookings]


@router.delete("/{booking_id}", response_model=BookingRead)
async def cancel_booking(booking_id: int, session: SessionDep) -> BookingRead:
    booking = await booking_service.cancel_booking(session, booking_id)
    return BookingRead.from_model(booking)
