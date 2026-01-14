import logging
import os
import random
from typing import Any
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
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

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant...""",
        )

        self.client = QdrantClient(
            url=os.getenv("QDRANT_ENDPOINT", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )

        self.collection_name = "knowledge_base"

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self.thinking_messages = [
            "Looking that up for you...",
            "One moment while I verify...",
            "Checking the documentation...",
        ]

    def get_thinking_message(self) -> str:
        return random.choice(self.thinking_messages)

    def embed(self, text: str):
        return self.embedder.encode(text).tolist()

    @function_tool()
    async def search_knowledge_base(
        self,
        context: RunContext,
        query: str,
        limit: int = 3,
    ) -> str:
        thinking = self.get_thinking_message()

        try:
            vector = self.embed(query)

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit,
            )

            if not results:
                return f"{thinking} I couldn’t find anything relevant."

            texts = []
            for point in results:
                payload = point.payload or {}
                text = payload.get("text") or payload.get("content")
                if text:
                    texts.append(text)

            if not texts:
                return f"{thinking} I found results, but no readable content."

            combined = "\n\n".join(texts)
            return f"{thinking}\nHere’s what I found:\n{combined}"

        except Exception as e:
            logger.exception("Qdrant search failed")
            return f"I ran into an error while searching: {str(e)}"

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
            # base_url="http://localhost:11435/v1", # uncomment for local testing
            model="Systran/faster-whisper-small",
            api_key="no-key-needed"
        ),
        llm=openai.LLM(
            base_url=llama_base_url,
            # base_url="http://localhost:11436/v1", # uncomment for local testing
            model=llama_model,
            api_key="no-key-needed"
        ),
        tts=openai.TTS(
            base_url="http://kokoro:8880/v1",
            # base_url="http://localhost:8880/v1", # uncomment for local testing
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
