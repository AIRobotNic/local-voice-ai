import os
from livekit_agent.src.rag.client_qdrant import QdrantClient
from .embedder import Embedder
from .chunker import chunk_text
from pypdf import PdfReader
import uuid

class Ingestor:
    def __init__(self, collection_name="knowledge_base"):
        self.client = QdrantClient(url=os.getenv("QDRANT_ENDPOINT", "http://localhost:6333"))
        self.embedder = Embedder()
        self.collection_name = collection_name

    def ingest_text(self, text: str, source="unknown"):
        chunks = chunk_text(text)

        points = []
        for chunk in chunks:
            vector = self.embedder.encode(chunk)

            points.append({
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "text": chunk,
                    "source": source,
                },
            })

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def ingest_pdf(self, path: str):
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        self.ingest_text(text, source=path)
