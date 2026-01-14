import logging
import os
import random
from typing import Any, List
from rag.retriever import QdrantRetriever
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    function_tool,
    RunContext,
)
from livekit.plugins import silero, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import openlit
openlit.init()

logger = logging.getLogger("agent")
load_dotenv(".env.local")

# -------------------- RAG COMPONENTS --------------------

class Embedder:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()


class Retriever:
    def __init__(self, collection_name="knowledge_base"):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_ENDPOINT", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self.embedder = Embedder()
        self.collection_name = collection_name

    def search(self, query: str, limit=3) -> List[str]:
        vector = self.embedder.encode(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
        )

        texts = []
        for r in results:
            payload = r.payload or {}
            if "text" in payload:
                texts.append(payload["text"])

        return texts

# -------------------- AGENT --------------------

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant.
You answer using the provided context when available.
If you don't know something, you say so honestly.
Your answers are concise, natural, and friendly.""",
        )

        # Подключаем RAG
        self.retriever = QdrantRetriever()
        self.collection_name = "knowledge_base"

        @function_tool()
        async def search_knowledge_base(self, context: RunContext, query: str) -> str:
            """Ищет информацию в базе знаний"""
            return self.retriever.search(query)

        self.thinking_messages = [
            "Looking that up for you...",
            "One moment while I check...",
            "Searching my knowledge...",
        ]

    def get_thinking_message(self) -> str:
        return random.choice(self.thinking_messages)

    @function_tool()
    async def multiply_numbers(
        self,
        context: RunContext,
        number1: int,
        number2: int,
    ) -> str:
        return f"The product of {number1} and {number2} is {number1 * number2}."

    @function_tool()
    async def search_knowledge_base(
        self,
        context: RunContext,
        query: str,
        limit: int = 3,
    ) -> str:
        """
        Search the knowledge base using semantic search.

        Args:
            query: What to search for
            limit: Number of results
        """

        thinking = self.get_thinking_message()

        try:
            results = self.retriever.search(query, limit=limit)

            if not results:
                return f"{thinking} I couldn't find anything relevant."

            context_block = "\n\n".join(results)

            return (
                f"{thinking}\n\n"
                f"Here is the relevant context:\n"
                f"{context_block}"
            )

        except Exception as e:
            logger.exception("Qdrant search failed")
            return f"I ran into an error while searching: {str(e)}"

# -------------------- SERVER --------------------

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    llama_model = os.getenv("LLAMA_MODEL", "qwen3-4b")
    llama_base_url = os.getenv("LLAMA_BASE_URL", "http://llama_cpp:11434/v1")

    session = AgentSession(
        stt=openai.STT(
            base_url="http://whisper:80/v1",
            model="Systran/faster-whisper-small",
            api_key="no-key-needed"
        ),
        llm=openai.LLM(
            base_url=llama_base_url,
            model=llama_model,
            api_key="no-key-needed"
        ),
        tts=openai.TTS(
            base_url="http://kokoro:8880/v1",
            model="kokoro",
            voice="af_nova",
            api_key="no-key-needed"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
