import redis.asyncio as redis
from src.core.config import settings

redis_pool = redis.ConnectionPool.from_url(
    str(settings.REDIS_URL),
    max_connections=50,
    decode_responses=True,
    socket_timeout=5.0
)

redis_client = redis.Redis(connection_pool=redis_pool)