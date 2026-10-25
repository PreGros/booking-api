from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import TSTZRANGE, ExcludeConstraint, Range
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Resource(Base):
    """Something that can be booked: a room, a table, a consultant..."""

    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    bookings: Mapped[list["Booking"]] = relationship(back_populates="resource")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        ExcludeConstraint(
            ("resource_id", "="),
            ("during", "&&"),
            where="status = 'confirmed'",
            using="gist",
            name="no_overlapping_bookings",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"))
    customer_email: Mapped[str] = mapped_column(String(255))
    during: Mapped[Range[datetime]] = mapped_column(TSTZRANGE)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    resource: Mapped[Resource] = relationship(back_populates="bookings")
