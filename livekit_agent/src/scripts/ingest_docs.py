import os
from pathlib import Path

from dotenv import load_dotenv

from rag.ingest import Ingestor


def main() -> None:
    """
    Simple helper script to ingest all text files from src/data/docs into Qdrant.

    Usage (from livekit_agent directory, with uv installed):
        uv run python -m src.scripts.ingest_docs
    """

    load_dotenv(".env.local")

    base_dir = Path(__file__).resolve().parent.parent
    docs_dir = base_dir / "data" / "docs"

    collection_name = os.getenv("QDRANT_COLLECTION", "knowledge_base")
    ingestor = Ingestor(collection_name=collection_name)

    for path in docs_dir.glob("*.txt"):
        with path.open("r", encoding="utf-8") as f:
            text = f.read()
        ingestor.ingest_text(text, source=str(path))


if __name__ == "__main__":
    main()

