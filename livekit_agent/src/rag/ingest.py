import os
import uuid
from .embedder import Embedder
from .chunker import chunk_text
from .client_qdrant import get_client  # <- правильный импорт
from pypdf import PdfReader


class Ingestor:
    def __init__(self, collection_name="knowledge_base"):
        """
        Инициализация инжестора:
        - создаём клиента Qdrant через get_client()
        - создаём экземпляр Embedder
        - сохраняем имя коллекции
        """
        self.client = get_client(
            url=os.getenv("QDRANT_ENDPOINT", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self.embedder = Embedder()
        self.collection_name = collection_name

    def ingest_text(self, text: str, source="unknown"):
        """
        Инжестим обычный текст в Qdrant
        """
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
        """
        Инжестим PDF документ
        """
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        self.ingest_text(text, source=path)
