from qdrant_client import QdrantClient

def get_client(url=None, api_key=None):
    return QdrantClient(
        url=url or "http://localhost:6333",
        api_key=api_key,
    )
