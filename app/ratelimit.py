from fastapi import Request

from app.cache import RedisDep
from app.config import settings
from app.errors import RateLimitExceeded


async def rate_limit(request: Request, redis: RedisDep) -> None:
    ip = request.client.host if request.client else "unknown"
    route = request.scope.get("route")
    path = route.path if route else request.url.path
    key = f"ratelimit:{request.method}:{path}:{ip}"

    async with redis.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, settings.rate_limit_window, nx=True)
        pipe.ttl(key)
        count, _, ttl = await pipe.execute()

    if count > settings.rate_limit_requests:
        raise RateLimitExceeded(headers={"Retry-After": str(max(ttl, 1))})
