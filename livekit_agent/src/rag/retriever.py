import random
from .client_qdrant import get_client
from qdrant_client.models import Filter, FieldCondition, MatchText

class QdrantRetriever:
    def __init__(self, collection_name: str = "knowledge_base"):
        from dotenv import load_dotenv
        import os

        load_dotenv(".env.local")
        self.client = QdrantClient(
            url=os.getenv("QDRANT_ENDPOINT", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self.collection_name = collection_name
        self.thinking_messages = [
            "Сейчас посмотрю...",
            "Подождите минутку, проверяю...",
            "Ищу информацию в базе...",
        ]

    def get_thinking_message(self) -> str:
        return random.choice(self.thinking_messages)

    def search(self, query: str, limit: int = 3) -> str:
        thinking = self.get_thinking_message()

        try:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="text", match=MatchText(text=query))]
                ),
                limit=limit
            )
        except Exception as e:
            return f"{thinking} Произошла ошибка при поиске: {e}"

        if not points or len(points) == 0:
            return f"{thinking} Ничего не найдено."

        texts = [p.payload.get("text") for p in points if p.payload.get("text")]
        if not texts:
            return f"{thinking} Нашел результаты, но нет текста."

        combined = "\n\n".join(texts)
        return f"{thinking}\nВот что я нашел:\n{combined}"
