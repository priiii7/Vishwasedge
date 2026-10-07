# Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ CLIENT LAYER — React 18 + Vite + Zustand + React Query        │
└───────────────────────────┬─────────────────────────────────┘
                             │ HTTPS (JWT / API key)
┌───────────────────────────▼─────────────────────────────────┐
│ API GATEWAY — FastAPI                                         │
│  auth · rate limiting (slowapi) · CORS · structlog · metrics  │
└───────────────────────────┬─────────────────────────────────┘
                             │
┌───────────────────────────▼─────────────────────────────────┐
│ ORCHESTRATION — orchestrator.py (DAS)                         │
│  ResourceMonitor (psutil) → simplify / offload / queue        │
│  router_agent → data_agent → reasoning_agent → grounding      │
└───────────────────────────┬─────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                     ▼
┌───────────────┐   ┌────────────────┐   ┌──────────────────────┐
│ HER retrieval  │   │ CGR grounding  │   │ LCE explainability    │
│ BM25 + Chroma  │   │ confidence     │   │ token-gradient        │
│ + RRF + rerank │   │ threshold 0.6  │   │ saliency (<5ms)        │
└───────────────┘   └────────────────┘   └──────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ AQR — llm_router.py scores complexity → fast / haiku / sonnet   │
│ llm_client.py — Anthropic API + circuit breaker + extractive    │
│ fallback (works with zero API key)                              │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ DATA — SQLite (users/documents/chunks/query_log) · Chroma       │
│ (persistent, embedded) · in-memory LRU cache (Redis optional)   │
└───────────────────────────────────────────────────────────────┘
```

## Request lifecycle (`POST /api/v1/query`)

1. **Auth** — `dependencies.py` validates JWT or API key, checks the `query` permission (RBAC).
2. **Validate** — `trust/validator.py` screens the query for unsafe patterns.
3. **Route** — `agents/router_agent.py` classifies intent (factual/analytical/procedural/safety).
4. **Resource check (DAS)** — `agents/orchestrator.py` snapshots CPU/RAM via `psutil`. If stressed: halves `max_docs` and downgrades the AQR tier (`simplify`).
5. **Complexity scoring (AQR)** — `models/llm_router.py` weighs reasoning indicators, domain term density, query length, context size, historical tier accuracy → picks `fast`/`haiku`/`sonnet`.
6. **Retrieve (HER)** — `agents/data_agent.py` runs BM25 + Chroma dense search, fuses with Reciprocal Rank Fusion, cross-encoder reranks the top candidates.
7. **Ground (CGR)** — `agents/grounding_agent.py` scores each chunk's confidence; drops anything below 0.6 with a stated reason.
8. **Reason** — `agents/reasoning_agent.py` calls `models/llm_client.py`, which either calls Claude (if configured, behind a circuit breaker) or falls back to deterministic extractive answering.
9. **Validate response** — lexical-overlap grounding check flags likely-ungrounded answers.
10. **Confidence** — `trust/confidence.py` blends retrieval quality + model confidence, Platt-scales it, buckets into high/medium/low.
11. **Explain (LCE)** — `trust/explainer.py` computes per-token saliency via leave-one-token-out re-embedding, generates template what-ifs.
12. **Respond** — structured JSON with response, confidence, tier, retrieval metadata, explanation; logged to `query_log` and Prometheus metrics.

## Resilience

- **Circuit breaker** (`models/llm_client.py`): 3 consecutive cloud-call failures trip it; extractive fallback serves traffic for 30s before retrying.
- **Cache fallback** (`infrastructure/redis_client.py`): in-memory LRU is the default; Redis is used automatically when `REDIS_URL` is reachable, with the same interface either way.
- **Embedding fallback** (`rag/embeddings.py`): if the HuggingFace model can't be downloaded, a deterministic hashing-trick embedder keeps retrieval functional offline.
- **Reranker fallback** (`rag/reranker.py`): if the cross-encoder can't load, falls back to normalized RRF fused scores.
