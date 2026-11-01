from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import AwareDatetime

from app.auth import require_role
from app.cache import AVAILABILITY_TTL, RedisDep, availability_field, availability_key
from app.db import SessionDep
from app.models import Role
from app.ratelimit import rate_limit
from app.schemas import AvailabilityOut, BusyInterval, ResourceCreate, ResourceRead
from app.services import bookings
from app.services import resources as resource_service

router = APIRouter(prefix="/resources", tags=["resources"], dependencies=[Depends(rate_limit)])


@router.post(
    "",
    response_model=ResourceRead,
    status_code=201,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def create_resource(data: ResourceCreate, session: SessionDep):
    return await resource_service.create_resource(session, data)


@router.get("", response_model=list[ResourceRead])
async def list_resources(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return await resource_service.list_resources(session, limit, offset)


@router.get("/{resource_id}/availability", response_model=AvailabilityOut)
async def get_availability(
    resource_id: int,
    session: SessionDep,
    redis: RedisDep,
    start: AwareDatetime,
    end: AwareDatetime,
) -> AvailabilityOut:
    if end <= start:
        raise HTTPException(status_code=422, detail="end must be after start")

    key = availability_key(resource_id)
    field = availability_field(start, end)

    cached = await redis.hget(key, field)
    if cached is not None:
        return AvailabilityOut.model_validate_json(cached)

    rows = await bookings.get_busy_intervals(session, resource_id, start, end)
    result = AvailabilityOut(
        resource_id=resource_id,
        start=start,
        end=end,
        busy=[BusyInterval(start=b.during.lower, end=b.during.upper) for b in rows],
    )
    await redis.hset(key, field, result.model_dump_json())
    await redis.expire(key, AVAILABILITY_TTL)
    return result
