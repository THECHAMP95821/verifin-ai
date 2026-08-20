from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
from src.core.config import settings

# Global Qdrant Client Singleton
qdrant_client = AsyncQdrantClient(
    url=str(settings.QDRANT_URL),
    api_key=settings.QDRANT_API_KEY,
    timeout=15
)


async def init_qdrant_schema() -> None:
    """Creates the vector collection on startup if it does not exist."""
    collections_res = await qdrant_client.get_collections()
    existing = {c.name for c in collections_res.collections}

    if settings.COLLECTION_NAME not in existing:
        await qdrant_client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.VECTOR_DIMENSION,
                distance=Distance.COSINE
            )
        )