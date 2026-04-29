"""
Vector store management for knowledge base.

Falls back to simple keyword retriever when Chroma/embeddings are not available.
"""

from pathlib import Path

from app.core.config import settings
from app.core.paths import DATA_DIR


def get_chroma_dir() -> Path:
    """Return the Chroma persist directory."""
    return DATA_DIR / "vector_store" / "chroma"


def is_chroma_available() -> bool:
    """Check if ChromaDB can be imported."""
    try:
        import chromadb  # noqa: F401
        return True
    except ImportError:
        return False


def get_vector_store():
    """
    Initialize and return a Chroma vector store.
    Raises ImportError if chromadb is not installed.
    """
    try:
        from langchain_chroma import Chroma
    except ImportError:
        raise ImportError(
            "langchain-chroma is not installed. "
            "Run: pip install langchain-chroma chromadb"
        )

    persist_dir = get_chroma_dir()
    persist_dir.mkdir(parents=True, exist_ok=True)

    store = Chroma(
        collection_name="dramatype_knowledge",
        persist_directory=str(persist_dir),
    )
    return store
