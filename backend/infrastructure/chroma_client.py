"""ChromaDB persistent client — embedded, no server process required."""

from functools import lru_cache
from typing import Any

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "vishwasedge_chunks"


@lru_cache(maxsize=1)
def get_chroma_collection() -> Any:
    import chromadb

    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    logger.info("chroma_ready", path=settings.chroma_persist_dir, count=collection.count())
    return collection
