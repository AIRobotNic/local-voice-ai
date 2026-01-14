from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import os

client = QdrantClient(url=os.getenv("QDRANT_ENDPOINT", "http://localhost:6333"))

client.recreate_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

print("Collection created")

