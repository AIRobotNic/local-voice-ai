import time
import os

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

QDRANT_URL = os.getenv("QDRANT_ENDPOINT", "http://qdrant:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "knowledge_base")
VECTOR_SIZE = 384


def wait_for_qdrant(client: QdrantClient, retries: int = 60, delay: float = 2.0) -> None:
    for i in range(retries):
        try:
            client.get_collections()
            print("✅ Qdrant is available")
            return
        except Exception as e:
            print(f"⏳ Waiting for Qdrant... ({i + 1}/{retries})")
            time.sleep(delay)

    raise RuntimeError("❌ Qdrant is not available")


def main() -> None:
    print(f"Connecting to Qdrant at: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL)

    wait_for_qdrant(client)

    if client.collection_exists(COLLECTION_NAME):
        print(f"ℹ️ Collection '{COLLECTION_NAME}' already exists")
        return

    print(f"🆕 Creating collection '{COLLECTION_NAME}'")

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

    print("✅ Collection created successfully")


if __name__ == "__main__":
    main()
