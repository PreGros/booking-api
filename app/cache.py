from datetime import datetime
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.config import settings

AVAILABILITY_TTL = 60  # seconds


def create_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


RedisDep = Annotated[Redis, Depends(get_redis)]


def availability_key(resource_id: int) -> str:
    return f"availability:{resource_id}"


def availability_field(start: datetime, end: datetime) -> str:
    return f"{start.isoformat()}|{end.isoformat()}"