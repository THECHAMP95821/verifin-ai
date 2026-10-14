from fastembed import TextEmbedding
import asyncio

class LocalEmbeddingService:

  def __init__(
      self,
      model_name: str = "BAAI/bge-large-en-v1.5",
      threads: int | None = None,
  ) -> None:
    self.model = TextEmbedding(model_name=model_name, threads=threads)

  async def embed_batch_async(
      self, texts: list[str], batch_size: int = 64
  ) -> list[list[float]]:
    return await asyncio.to_thread(
        self._embed_batch_sync, texts=texts, batch_size=batch_size
    )

  def _embed_batch_sync(
      self, texts: list[str], batch_size: int = 64
  ) -> list[list[float]]:
    if not texts:
      return []
    embeddings_generator = self.model.embed(texts, batch_size=batch_size)
    return [vec.tolist() for vec in embeddings_generator]