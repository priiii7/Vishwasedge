"""HER: Hybrid Edge Retrieval — BM25 (sparse) + Chroma (dense) fused with
Reciprocal Rank Fusion, per the spec's §Phase 3 pseudocode.
"""

import re
from dataclasses import dataclass, field
from threading import Lock

from rank_bm25 import BM25Okapi

from backend.core.logging import get_logger
from backend.infrastructure.chroma_client import get_chroma_collection
from backend.rag.embeddings import get_embedder

logger = get_logger(__name__)

RRF_K = 60


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    document_id: str
    source: str
    bm25_rank: int | None = None
    vector_rank: int | None = None
    fused_score: float = 0.0
    rerank_score: float | None = None
    confidence: float = 0.0


class _BM25Index:
    """In-process BM25 index rebuilt incrementally as documents are ingested."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._ids: list[str] = []
        self._corpus: list[list[str]] = []
        self._meta: dict[str, dict] = {}
        self._bm25: BM25Okapi | None = None

    def add(self, chunk_id: str, text: str, meta: dict) -> None:
        with self._lock:
            self._ids.append(chunk_id)
            self._corpus.append(_tokenize(text))
            self._meta[chunk_id] = {"text": text, **meta}
            self._bm25 = BM25Okapi(self._corpus) if self._corpus else None

    def search(self, query: str, k: int) -> list[tuple[str, float]]:
        with self._lock:
            if self._bm25 is None:
                return []
            scores = self._bm25.get_scores(_tokenize(query))
            ranked = sorted(zip(self._ids, scores), key=lambda x: x[1], reverse=True)
            return [(cid, score) for cid, score in ranked[:k] if score > 0]

    def get_meta(self, chunk_id: str) -> dict:
        return self._meta.get(chunk_id, {})


_bm25_index = _BM25Index()


def get_bm25_index() -> _BM25Index:
    return _bm25_index


def index_chunk(chunk_id: str, text: str, document_id: str, source: str) -> None:
    """Add a chunk to both the sparse (BM25) and dense (Chroma) indexes."""
    _bm25_index.add(chunk_id, text, {"document_id": document_id, "source": source})

    collection = get_chroma_collection()
    embedder = get_embedder()
    vector = embedder.encode(text).tolist()
    collection.add(
        ids=[chunk_id],
        embeddings=[vector],
        documents=[text],
        metadatas=[{"document_id": document_id, "source": source}],
    )


def _vector_search(query: str, k: int) -> list[tuple[str, float]]:
    collection = get_chroma_collection()
    if collection.count() == 0:
        return []
    embedder = get_embedder()
    query_vector = embedder.encode(query).tolist()
    results = collection.query(query_embeddings=[query_vector], n_results=min(k, collection.count()))
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    # Chroma cosine distance -> similarity for readability (not used in RRF math, ranks are)
    return list(zip(ids, [1 - d for d in distances]))


def hybrid_search(query: str, k: int = 15, alpha: float = 0.5) -> list[RetrievedChunk]:
    """BM25 + Chroma, fused with Reciprocal Rank Fusion.

        fused_scores[doc] += alpha * (1 / (RRF_K + bm25_rank + 1))
        fused_scores[doc] += (1-alpha) * (1 / (RRF_K + vector_rank + 1))
    """
    bm25_results = _bm25_index.search(query, k)
    vector_results = _vector_search(query, k)

    fused: dict[str, RetrievedChunk] = {}

    for rank, (chunk_id, _score) in enumerate(bm25_results):
        meta = _bm25_index.get_meta(chunk_id)
        chunk = fused.setdefault(
            chunk_id,
            RetrievedChunk(
                chunk_id=chunk_id,
                text=meta.get("text", ""),
                document_id=meta.get("document_id", ""),
                source=meta.get("source", ""),
            ),
        )
        chunk.bm25_rank = rank
        chunk.fused_score += alpha * (1.0 / (RRF_K + rank + 1))

    collection = get_chroma_collection()
    for rank, (chunk_id, _score) in enumerate(vector_results):
        if chunk_id not in fused:
            got = collection.get(ids=[chunk_id], include=["documents", "metadatas"])
            text = got["documents"][0] if got["documents"] else ""
            meta = got["metadatas"][0] if got["metadatas"] else {}
            fused[chunk_id] = RetrievedChunk(
                chunk_id=chunk_id,
                text=text,
                document_id=meta.get("document_id", ""),
                source=meta.get("source", ""),
            )
        fused[chunk_id].vector_rank = rank
        fused[chunk_id].fused_score += (1 - alpha) * (1.0 / (RRF_K + rank + 1))

    return sorted(fused.values(), key=lambda c: c.fused_score, reverse=True)
