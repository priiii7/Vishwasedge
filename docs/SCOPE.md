# Scope: what's real vs. deferred

This build implements the VishwasEdge spec's architecture and all 5 "novel" components with working code, adapted to run with **zero manual installs and no multi-GB downloads**. Full rationale in the build plan; summary here:

## Implemented for real

- HER hybrid retrieval (BM25 + Chroma + RRF fusion + cross-encoder rerank)
- CGR confidence-grounded filtering (0.6 threshold, stated reasons)
- DAS resource-aware degradation (psutil CPU/RAM snapshot → simplify/offload)
- LCE token-gradient saliency explanations (leave-one-token-out, no LLM call)
- AQR complexity-scored tier routing (fast/haiku/sonnet)
- JWT + API key auth, bcrypt password hashing, RBAC (admin/operator/viewer)
- SQLite + SQLAlchemy + Alembic migrations (users, documents, chunks, query_log)
- structlog JSON logging, Prometheus `/metrics`, `/health` + `/ready` checks
- PDF/DOCX/TXT ingestion → semantic chunking → indexing
- Circuit breaker around cloud LLM calls with extractive fallback
- SSE streaming endpoint
- React frontend: chat, trust dashboard, confidence meter, token heatmap, source attribution, document upload, dark mode, JWT-authenticated
- Unit + integration tests (29 tests, 81% backend coverage)

## Adapted from the original spec (and why)

| Spec asked for | This build uses | Why |
|---|---|---|
| Postgres | SQLite (same SQLAlchemy/Alembic layer) | No server to install |
| Required Redis | In-memory LRU by default, Redis if `REDIS_URL` set | Spec's own fallback made the default |
| Local llama.cpp + Qwen2.5-7B/Phi-4 GGUF (multi-GB) | Anthropic API (Haiku/Sonnet) if `ANTHROPIC_API_KEY` set, else deterministic extractive answering | No large downloads, no GPU requirement, works with zero config |
| Whoosh | `rank-bm25` | Pure Python, no compiled index |

## Written as code/config but not executed here

- `tests/load/locustfile.py` — needs a live server + a deliberate load run
- `docker/Dockerfile.edge` multi-arch build — needs Docker buildx and takes a long time
- `.github/workflows/*` — needs to actually run in GitHub Actions
- `docs/PAPER.md` — full outline and content, not compiled to LaTeX/PDF
- Grafana/Prometheus/Jaeger servers — compose config included, not started
- The 500-question oil-gas benchmark dataset and n=50 human trust-score study — need real data collection this session doesn't have
