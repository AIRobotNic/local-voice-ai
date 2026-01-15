import time

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

import os
from dotenv import load_dotenv

load_dotenv(".env.local")
QDRANT_URL = os.getenv("QDRANT_ENDPOINT", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "knowledge_base")
VECTOR_SIZE = 384


def wait_for_qdrant(client: QdrantClient, retries: int = 60, delay: float = 2.0) -> None:
    for i in range(retries):
        try:
            client.get_collections()
            return
        except Exception:
            print(f"Waiting for Qdrant... ({i + 1}/{retries})")
            time.sleep(delay)
    raise RuntimeError("Qdrant is not available")


def main() -> None:
    client = QdrantClient(url=QDRANT_URL)

    # 1. Ждём готовности Qdrant
    wait_for_qdrant(client)

    # 2. Создаём коллекцию ТОЛЬКО если её нет
    if not client.collection_exists(COLLECTION_NAME):
        print(f"Creating collection '{COLLECTION_NAME}'")

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists")


if __name__ == "__main__":
    main()
