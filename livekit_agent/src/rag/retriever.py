import os
from typing import List

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from .embedder import Embedder


class QdrantRetriever:
    """Simple semantic retriever over a Qdrant collection."""

    def __init__(self, collection_name: str = "knowledge_base") -> None:
        load_dotenv(".env.local")
        self.client = QdrantClient(
            url=os.getenv("QDRANT_ENDPOINT", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self.collection_name = collection_name
        self.embedder = Embedder()

        # Ensure the collection exists with the correct vector size
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the collection if it doesn't exist yet."""
        collections = self.client.get_collections()
        if any(c.name == self.collection_name for c in collections.collections):
            return

        # all-MiniLM-L6-v2 outputs 384-dim vectors
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    def search(self, query: str, limit: int = 3) -> List[str]:
        """Return the most relevant text chunks for a query."""
        vector = self.embedder.encode(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
        )

        texts: List[str] = []
        for r in results:
            payload = r.payload or {}
            text = payload.get("text")
            if isinstance(text, str):
                texts.append(text)

        return texts
