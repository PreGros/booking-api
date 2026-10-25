from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import BookingConflict, BookingNotFound, ResourceNotFound
from app.models import Booking, Resource
from app.schemas import BookingCreate

OVERLAP_CONSTRAINT = "no_overlapping_bookings"


async def create_booking(session: AsyncSession, data: BookingCreate) -> Booking:
    if await session.get(Resource, data.resource_id) is None:
        raise ResourceNotFound

    booking = Booking(
        resource_id=data.resource_id,
        customer_email=data.customer_email,
        during=Range(data.start, data.end, bounds="[)"),
    )
    session.add(booking)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if OVERLAP_CONSTRAINT in str(exc.orig):
            raise BookingConflict from exc
        raise
    return booking


async def list_bookings(
    session: AsyncSession, resource_id: int | None, limit: int, offset: int
) -> list[Booking]:
    stmt = select(Booking).order_by(Booking.id).limit(limit).offset(offset)
    if resource_id is not None:
        stmt = stmt.where(Booking.resource_id == resource_id)
    return list((await session.scalars(stmt)).all())


async def cancel_booking(session: AsyncSession, booking_id: int) -> Booking:
    booking = await session.get(Booking, booking_id)
    if booking is None:
        raise BookingNotFound
    booking.status = "cancelled"  # frees the slot: the constraint only covers 'confirmed'
    await session.commit()
    return booking
