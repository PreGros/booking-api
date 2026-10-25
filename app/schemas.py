from datetime import datetime
from typing import Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models import Booking


class ResourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ResourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class BookingCreate(BaseModel):
    resource_id: int
    customer_email: EmailStr
    start: AwareDatetime  # timezone required, naive datetimes are rejected
    end: AwareDatetime

    @model_validator(mode="after")
    def end_after_start(self) -> Self:
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class BookingRead(BaseModel):
    id: int
    resource_id: int
    customer_email: str
    start: datetime
    end: datetime
    status: str

    # BookingRead.from_model(booking) converts a SQLAlchemy Booking into
    # a Pydantic BookingRead object
    @classmethod
    def from_model(cls, booking: Booking) -> Self:
        return cls(
            id=booking.id,
            resource_id=booking.resource_id,
            customer_email=booking.customer_email,
            start=booking.during.lower,
            end=booking.during.upper,
            status=booking.status,
        )
