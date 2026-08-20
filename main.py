from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import settings
from src.core.postgres import engine
from src.core.redis import redis_client
from src.core.qdrant import qdrant_client, init_qdrant_schema
import logfire

logfire.configure(
    service_name="verifin-ai-backend",
    send_to_logfire=True,
    token=settings.LOGFIRE_TOKEN,
)

# 2. Instrument Storage Drivers
logfire.instrument_sqlalchemy(engine.sync_engine)
logfire.instrument_redis(redis_client)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Phase
    with logfire.span("Application Startup Initialization"):
        await redis_client.ping()
        await init_qdrant_schema()
    yield
    # Shutdown Phase: Drain and close all socket connections
    with logfire.span("Application Graceful Teardown"):
        await engine.dispose()
        await redis_client.aclose()
        await qdrant_client.close()
    logfire.shutdown()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

logfire.instrument_fastapi(app, capture_headers=True)

@app.get("/")
def read_root():
    return {"Hello": "World"}