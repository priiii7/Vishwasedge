# VishwasEdge — Trustworthy Edge-Native Multi-Agent RAG

An offline-first, multi-agent RAG system with real-time trust scoring and explainability: every answer ships with a confidence score, source attribution, and a token-saliency explanation.

This build is a scoped implementation of the full VishwasEdge research spec — see [`docs/SCOPE.md`](docs/SCOPE.md) for exactly what's implemented for real vs. deferred, and why.

## Quick start (Windows)

**Backend**

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

**Frontend** (separate terminal)

```powershell
cd frontend
npm run dev
```

Then open http://localhost:5173 and sign in with the seeded default account:

- Username: `operator`
- Password: `changeme123`

(Change these via `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` in `.env` before first run in anything beyond a local demo.)

Upload a PDF/DOCX/TXT in the left panel, then ask a question about it in the chat. Click "Show trust dashboard" under any answer to see the confidence meter, token saliency heatmap, source attribution, and what-if explanations.

## Running fully offline vs. with cloud LLM tiers

By default (`ANTHROPIC_API_KEY` unset), the Adaptive Quantization Router's `haiku`/`sonnet` tiers fall back to a deterministic **extractive** answering mode — no LLM call, no internet required, answers are built directly from the retrieved document text. This is what makes the "no installs, no downloads, just works" requirement possible.

To get generative (not just extractive) answers, set `ANTHROPIC_API_KEY` in `.env` — the router will then call Claude Haiku or Sonnet depending on query complexity, with automatic fallback to extractive mode if the API call fails (circuit breaker in `backend/models/llm_client.py`).

## Architecture

Five components carry the spec's "novel contribution" claims — all implemented with real logic, not stubs:

| Component | File | What it does |
|---|---|---|
| **HER** (Hybrid Edge Retrieval) | `backend/rag/hybrid_retriever.py` | BM25 + Chroma dense search, fused via Reciprocal Rank Fusion, then cross-encoder re-ranked |
| **CGR** (Confidence-Grounded Retrieval) | `backend/agents/grounding_agent.py` | Per-chunk confidence scoring; chunks below 0.6 are filtered with a stated reason |
| **DAS** (Dynamic Agent Scheduling) | `backend/agents/orchestrator.py` | `psutil`-based resource snapshot drives simplify/offload/queue degradation under load |
| **LCE** (Lightweight Counterfactual Explanations) | `backend/trust/explainer.py` | Leave-one-token-out re-embedding + cosine distance — O(n), no LLM call |
| **AQR** (Adaptive Quantization Router) | `backend/models/llm_router.py` | Weighted complexity scoring routes each query to the cheapest tier that can handle it |

Full diagram in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), API reference in [`docs/API.md`](docs/API.md), paper outline in [`docs/PAPER.md`](docs/PAPER.md).

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=backend --cov-report=term-missing
```

## Deployment

- **Frontend** builds to static assets (`npm run build` → `frontend/dist`) — deploy directly to Vercel. Set `VITE_API_URL` to your backend's public URL as a Vercel environment variable.
- **Backend** needs a real Python process (ML deps, SQLite file, Chroma persistence) — it does **not** fit Vercel's serverless model. Deploy via `docker/Dockerfile.backend` to Render, Railway, Fly.io, or any VM. `docker/docker-compose.yml` brings up backend + frontend + Redis + Prometheus + Grafana together.
- **Edge devices**: `docker/Dockerfile.edge` + `scripts/deploy_edge.sh` target ARM64/x86_64 low-memory devices (Raspberry Pi 5, Intel N100).

## Benchmarking

```powershell
.\.venv\Scripts\python.exe scripts\benchmark.py --queries 20
```

Reports p50/p95 end-to-end, retrieval, and explanation latency against the spec's targets (150ms / 80ms / 5ms).
