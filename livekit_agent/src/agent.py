import logging
import os
from typing import Any

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
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# import openlit
# openlit.init()

logger = logging.getLogger("agent")

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant. The user is interacting with you via voice, even if you perceive the conversation as text.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333)),
            prefer_grpc=False
        )

    @function_tool()
    async def multiply_numbers(
        self,
        context: RunContext,
        number1: int,
        number2: int,
    ) -> dict[str, Any]:
        """Multiply two numbers.
        
        Args:
            number1: The first number to multiply.
            number2: The second number to multiply.
        """

        return f"The product of {number1} and {number2} is {number1 * number2}."

    @function_tool()
    async def store_memory(
        self,
        context: RunContext,
        key: str,
        value: str,
    ) -> dict[str, Any]:
        """Store information in memory using Qdrant.
        
        Args:
            key: The key to store the information under.
            value: The information to store.
        """
        try:
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name="agent_memory",
                points=[
                    {
                        "id": hash(key),
                        "vector": [float(x) for x in key.encode('utf-8')[:10]],  # Simple vectorization
                        "payload": {
                            "key": key,
                            "value": value,
                            "timestamp": context.session.start_time.isoformat()
                        }
                    }
                ]
            )
            return f"Stored information under key '{key}'"
        except Exception as e:
            return f"Failed to store information: {str(e)}"

    @function_tool()
    async def retrieve_memory(
        self,
        context: RunContext,
        key: str,
    ) -> dict[str, Any]:
        """Retrieve information from memory using Qdrant.
        
        Args:
            key: The key to retrieve information for.
        """
        try:
            # Search in Qdrant
            results = self.qdrant_client.search(
                collection_name="agent_memory",
                query_vector=[float(x) for x in key.encode('utf-8')[:10]],  # Simple vectorization
                limit=1
            )
            
            if results:
                return results[0].payload.get("value", "No value found")
            else:
                return "No information found for that key"
        except Exception as e:
            return f"Failed to retrieve information: {str(e)}"

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
