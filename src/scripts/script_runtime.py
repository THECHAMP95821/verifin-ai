# src/core/script_runtime.py
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
import logfire
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.postgres import AsyncSessionFactory, engine
from src.core.qdrant import init_qdrant_schema, qdrant_client
from src.core.redis import redis_client


@dataclass(slots=True)
class ScriptContext:
    session: AsyncSession
    redis: Redis
    qdrant: AsyncQdrantClient


@asynccontextmanager
async def run_script(service_name: str) -> AsyncGenerator[ScriptContext, None]:
    """
    Unified execution harness for CLI & batch worker scripts.
    - Configures Logfire with script-specific service namespace.
    - Instruments DB & Redis drivers.
    - Initializes Qdrant schema & tests Redis socket.
    - Manages transactional PostgreSQL session (auto-commits on success, rolls back on error).
    - Automatically closes socket pools and flushes Logfire telemetry on exit.
    """
    # 1. Initialize Logfire
    logfire.configure(
        token=settings.LOGFIRE_TOKEN,
        service_name=service_name,
        send_to_logfire=True,
    )
    logfire.instrument_sqlalchemy(engine.sync_engine)
    logfire.instrument_redis(redis_client)

    # 2. Boot checks
    await redis_client.ping()
    await init_qdrant_schema()

    # 3. Manage execution lifecycle
    async with AsyncSessionFactory() as session:
        try:
            with logfire.span(f"Executing Batch Script: {service_name}"):
                yield ScriptContext(session=session, redis=redis_client, qdrant=qdrant_client)
                await session.commit()
        except Exception as exc:
            await session.rollback()
            logfire.exception("Script failed with unhandled error", exc_info=exc)
            raise
        finally:
            # 4. Graceful teardown & synchronous log flush
            await engine.dispose()
            await redis_client.aclose()
            await qdrant_client.close()
            logfire.shutdown()