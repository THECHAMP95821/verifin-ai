from typing import Sequence
from uuid import UUID
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from src.schemas.qualitative_ingestion import ChildChunkDTO

class SecQualitativeRepo:
    def __init__(
            self,
            client: AsyncQdrantClient,
            collection_name: str = "sec_qualitative",
            vector_dim: int = 1024,  # BAAI/bge-large-en-v1.5 output dimension
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.vector_dim = vector_dim

    async def bulk_upsert_children(
            self,
            children: Sequence[ChildChunkDTO],
            batch_size: int = 100,
    ) -> int:
        """Converts ChildChunkDTOs into PointStruct objects and streams them in batches to Qdrant."""
        if not children:
            return 0

        total_children = len(children)
        total_upserted = 0

        for i in range(0, total_children, batch_size):
            batch_slice = children[i: i + batch_size]
            points: list[qmodels.PointStruct] = []

            for child in batch_slice:
                if child.embedding is None:
                    raise ValueError(
                        f"Cannot index child chunk {child.child_id} without an embedding."
                    )

                # Qdrant accepts UUID strings or integers as point IDs
                point_id_str = str(child.child_id)

                payload = {
                    "parent_id": child.parent_id,
                    "filing_id": child.filing.id,
                    "ticker": child.ticker,
                    "form_type": child.filing.filing_type,
                    "fiscal_year": child.filing.fiscal_year,
                    "text_payload": child.text_payload,
                    "cik": child.filing.cik,
                }

                points.append(
                    qmodels.PointStruct(
                        id=point_id_str,
                        vector=child.embedding,
                        payload=payload,
                    )
                )

            await self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )
            total_upserted += len(points)

        return total_upserted