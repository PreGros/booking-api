from typing import Annotated

from fastapi import APIRouter, Query

from app.db import SessionDep
from app.schemas import ResourceCreate, ResourceRead
from app.services import resources as resource_service

router = APIRouter(prefix="/resources", tags=["resources"])


@router.post("", response_model=ResourceRead, status_code=201)
async def create_resource(data: ResourceCreate, session: SessionDep):
    return await resource_service.create_resource(session, data)


@router.get("", response_model=list[ResourceRead])
async def list_resources(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return await resource_service.list_resources(session, limit, offset)
