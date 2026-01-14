import logging
import os
import random
from typing import Any

from dotenv import load_dotenv
from rag.retriever import QdrantRetriever

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
)
from livekit.plugins import openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import openlit

openlit.init()

logger = logging.getLogger("agent")
load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a helpful voice AI assistant. "
                "The user is interacting with you via voice, even if you perceive the conversation as text. "
                "You eagerly assist users with their questions by providing information from your own reasoning "
                "and from an external company knowledge base accessible via tools. "
                "When questions relate to the company, Its IT Group, its services or technical offerings, "
                "you should first call the knowledge base search tool to retrieve relevant context, "
                "then use that context to craft your answer. "
                "If you do not know something and cannot find it in the knowledge base, say so honestly. "
                "Your responses are concise, natural, friendly, and avoid special formatting characters."
            ),
        )

        self.retriever = QdrantRetriever(collection_name="knowledge_base")
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
        """Multiply two numbers and return a short explanation."""

        return f"The product of {number1} and {number2} is {number1 * number2}."

    @function_tool()
    async def search_knowledge_base(
        self,
        context: RunContext,
        query: str,
        limit: int = 3,
    ) -> str:
        """
        Search the Qdrant-powered knowledge base for relevant information.

        Args:
            query: What to search for.
            limit: Maximum number of result chunks to include.
        """

        thinking = self.get_thinking_message()

        try:
            results = self.retriever.search(query, limit=limit)

            if not results:
                return f"{thinking} I couldn't find anything relevant in the knowledge base."

            context_block = "\n\n".join(results)

            return (
                f"{thinking}\n\n"
                f"Here is the relevant context from the knowledge base:\n"
                f"{context_block}"
            )

        except Exception as e:
            logger.exception("Qdrant search failed")
            return f"I ran into an error while searching the knowledge base: {str(e)}"


server = AgentServer()


def prewarm(proc: JobProcess) -> None:
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
            api_key="no-key-needed",
        ),
        llm=openai.LLM(
            base_url=llama_base_url,
            model=llama_model,
            api_key="no-key-needed",
        ),
        tts=openai.TTS(
            base_url="http://kokoro:8880/v1",
            model="kokoro",
            voice="af_nova",
            api_key="no-key-needed",
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
