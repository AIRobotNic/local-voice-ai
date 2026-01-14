import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv(".env.local")

client = QdrantClient(url=os.getenv("QDRANT_ENDPOINT", "http://localhost:6333"))

client.recreate_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

print("Collection created")

