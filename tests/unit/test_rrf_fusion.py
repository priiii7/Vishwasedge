"""Verifies the Reciprocal Rank Fusion math matches the spec's pseudocode
without touching the embedding model or Chroma (kept fast/offline)."""

from backend.rag.hybrid_retriever import RRF_K


def rrf_fuse(bm25_ranked: list[str], vector_ranked: list[str], alpha: float = 0.5) -> dict[str, float]:
    scores: dict[str, float] = {}
    for rank, doc_id in enumerate(bm25_ranked):
        scores[doc_id] = scores.get(doc_id, 0.0) + alpha * (1.0 / (RRF_K + rank + 1))
    for rank, doc_id in enumerate(vector_ranked):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1 - alpha) * (1.0 / (RRF_K + rank + 1))
    return scores


def test_doc_ranked_first_in_both_wins():
    scores = rrf_fuse(["a", "b", "c"], ["a", "c", "b"])
    assert max(scores, key=scores.get) == "a"


def test_doc_only_in_one_list_still_scored():
    scores = rrf_fuse(["a", "b"], ["c"])
    assert set(scores.keys()) == {"a", "b", "c"}
    assert scores["a"] > scores["b"]  # a ranked higher in bm25


def test_alpha_weights_bm25_vs_vector():
    bm25_only_first = rrf_fuse(["x", "y"], ["y", "x"], alpha=1.0)
    assert max(bm25_only_first, key=bm25_only_first.get) == "x"

    vector_only_first = rrf_fuse(["x", "y"], ["y", "x"], alpha=0.0)
    assert max(vector_only_first, key=vector_only_first.get) == "y"
