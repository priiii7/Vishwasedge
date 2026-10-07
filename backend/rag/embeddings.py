"""Embedding backend: SentenceTransformer with an offline hashing fallback.

If the HuggingFace model can't be downloaded (no internet, blocked egress),
we fall back to a deterministic hashing-trick embedding so the system still
boots and answers queries instead of hard-failing — in the spirit of the
spec's "98% offline success" target.
"""

import hashlib
import math
import re
from functools import lru_cache

import numpy as np

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

HASH_DIM = 384  # matches all-MiniLM-L6-v2 output dim for drop-in compatibility


class HashingEmbedder:
    """Pure-Python offline fallback: token-hash bag-of-words, L2-normalized."""

    dim = HASH_DIM

    def encode(self, texts: list[str] | str, **_kwargs) -> np.ndarray:
        single = isinstance(texts, str)
        items = [texts] if single else texts
        vectors = np.array([self._embed_one(t) for t in items], dtype=np.float32)
        return vectors[0] if single else vectors

    def _embed_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        for tok in tokens:
            idx = int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec


class SentenceTransformerEmbedder:
    dim = 384

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str] | str, **kwargs) -> np.ndarray:
        return self._model.encode(texts, normalize_embeddings=True, **kwargs)


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformerEmbedder | HashingEmbedder:
    settings = get_settings()
    try:
        embedder = SentenceTransformerEmbedder(settings.embedding_model)
        logger.info("embedder_loaded", backend="sentence-transformers", model=settings.embedding_model)
        return embedder
    except Exception as exc:  # noqa: BLE001
        logger.warning("embedder_fallback", reason=str(exc))
        return HashingEmbedder()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-8
    return float(np.dot(a, b) / denom)


@lru_cache(maxsize=4096)
def _cached_encode_single(text: str) -> tuple:
    embedder = get_embedder()
    vec = embedder.encode(text)
    return tuple(float(x) for x in vec)


def encode_cached(text: str) -> np.ndarray:
    """LRU-cached single-string embedding — hot path for LCE saliency perturbations."""
    return np.array(_cached_encode_single(text), dtype=np.float32)


def is_nan_safe(x: float) -> float:
    return 0.0 if math.isnan(x) else x
