from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import BookingConflict, BookingNotFound, ResourceNotFound
from app.models import Booking, Resource, Role, User
from app.schemas import BookingCreate

OVERLAP_CONSTRAINT = "no_overlapping_bookings"


async def create_booking(session: AsyncSession, data: BookingCreate, user_id: int) -> Booking:
    if await session.get(Resource, data.resource_id) is None:
        raise ResourceNotFound

    booking = Booking(
        user_id=user_id,
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
    session: AsyncSession, resource_id: int | None, limit: int, offset: int, user_id: int | None = None
) -> list[Booking]:
    stmt = select(Booking).order_by(Booking.id).limit(limit).offset(offset)
    if resource_id is not None:
        stmt = stmt.where(Booking.resource_id == resource_id)
    if user_id is not None:
        stmt = stmt.where(Booking.user_id == user_id)
    return list((await session.scalars(stmt)).all())


async def cancel_booking(session: AsyncSession, booking_id: int, user: User) -> Booking:
    booking = await session.get(Booking, booking_id)
    if booking is None or (user.role != Role.ADMIN and booking.user_id != user.id):
        raise BookingNotFound
    booking.status = "cancelled"  # frees the slot: the constraint only covers 'confirmed'
    await session.commit()
    return booking


async def get_busy_intervals(
    session: AsyncSession, resource_id: int, start: datetime, end: datetime
) -> list[Booking]:
    if await session.get(Resource, resource_id) is None:
        raise ResourceNotFound

    stmt = (
        select(Booking)
        .where(
            Booking.resource_id == resource_id,
            Booking.status == "confirmed",
            Booking.during.overlaps(Range(start, end, bounds="[)")),
        )
        .order_by(func.lower(Booking.during))
    )
    result = await session.scalars(stmt)
    return list(result)
