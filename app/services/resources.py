from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ResourceAlreadyExists
from app.models import Resource
from app.schemas import ResourceCreate


async def create_resource(session: AsyncSession, data: ResourceCreate) -> Resource:
    resource = Resource(name=data.name)
    session.add(resource)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ResourceAlreadyExists from exc
    return resource


async def list_resources(session: AsyncSession, limit: int, offset: int) -> list[Resource]:
    stmt = select(Resource).order_by(Resource.id).limit(limit).offset(offset)
    return list((await session.scalars(stmt)).all())
