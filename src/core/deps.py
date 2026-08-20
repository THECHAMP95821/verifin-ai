from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
# from qdrant_client import AsyncQdrantClient

from src.core.postgres import AsyncSessionFactory
from src.core.redis import redis_client
# from src.core.qdrant import qdrant_client

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Per-request Unit of Work.
    Opens an isolated transaction, commits on success,
    rolls back on unhandled error, and closes the session.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_redis_client() -> Redis:
    return redis_client

# def get_qdrant_client() -> AsyncQdrantClient:
#     return qdrant_client