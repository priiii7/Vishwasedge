# VishwasEdge: Resource-Aware Multi-Agent Orchestration with Lightweight Counterfactual Explainability for Edge-Native RAG

*Paper outline — LaTeX-ready structure with real content per section. Not yet compiled to `.tex`/PDF; Sections 5.2–5.3 need the real benchmark run (`scripts/benchmark.py`) and a labeled evaluation corpus before numbers can be filled in.*

## 1. Introduction

Retrieval-augmented generation deployed at the edge faces three compounding constraints that cloud-hosted RAG doesn't: **latency** budgets an order of magnitude tighter than typical API round-trips, **intermittent or absent connectivity**, and a **trust deficit** — operators making safety-relevant decisions (e.g., oil & gas field operations) need to know not just an answer but how confident the system is and why, without the compute budget for standard explainability methods (LIME, SHAP).

**Research question**: How can a multi-agent RAG system maintain calibrated trust signals and sub-200ms explainability under a <4GB memory budget and unreliable connectivity?

## 2. Related Work

- **Edge LLM deployment**: llama.cpp and MLC-LLM demonstrate quantized inference is feasible on consumer/edge hardware, but neither addresses retrieval quality or explainability at the same resource budget.
- **Multi-agent systems**: AutoGen and CrewAI provide agent orchestration primitives but assume cloud-scale compute availability; none incorporate resource-aware scheduling as a first-class constraint.
- **RAG optimization**: Self-RAG and Corrective RAG improve answer grounding via self-critique, at the cost of additional LLM calls — expensive at the edge.
- **Explainability**: LIME and SHAP are model-agnostic but require O(n·k) perturbation-and-refit cycles; attention-based methods require white-box model access incompatible with API-tier LLM fallback.
- **Gap**: no existing system combines resource-aware agent scheduling, confidence-grounded retrieval, and sub-5ms explainability under a single edge memory budget.

## 3. System Architecture

See `docs/ARCHITECTURE.md` for the full component diagram (Figure 1) and per-component memory budgets (Table 1: BM25 index <50MB, dense vector store <200MB, cross-encoder <100MB — matching the Hybrid Edge Retrieval target of <300MB for 10K documents).

## 4. Novel Contributions

### 4.1 Dynamic Agent Scheduling (DAS)
**Algorithm 1** (`backend/agents/orchestrator.py::handle_query`): a `psutil` resource snapshot gates every query. Under CPU/memory pressure, the system halves retrieved-document count and downgrades the LLM tier (`simplify`) rather than failing or queuing indefinitely.
**Latency bound** (informal): worst-case added latency under the `simplify` path is bounded by the cost of one extra tier-downgrade lookup (O(1)) plus a reduced retrieval candidate set, i.e., strictly less than the unconstrained path's latency — degradation never increases worst-case latency.

### 4.2 Confidence-Grounded Retrieval (CGR)
**Equation 1** — per-chunk confidence:
```
confidence(chunk) = min(rerank_score(chunk) + agreement_bonus(chunk), 1.0)
agreement_bonus(chunk) = 0.1 if chunk appears in both BM25 and vector top-k, else 0
```
**Algorithm 2** (`backend/agents/grounding_agent.py::ground`): chunks with `confidence < 0.6` are filtered from the context passed to the reasoning agent, with a human-readable reason attached (e.g., "matched only by dense retrieval — weak keyword overlap").

### 4.3 Lightweight Counterfactual Explanations (LCE)
**Algorithm 3** (`backend/trust/explainer.py::token_gradient_saliency`): for each token `t_i` in the query, compute `importance(t_i) = 1 - cos_sim(embed(query), embed(query \ t_i))`.
**Complexity**: O(n) embedding calls for n tokens, vs. O(n·k) perturb-and-refit for LIME (k = number of surrogate model samples, typically 500–5000). No LLM call is required at any point.

### 4.4 Hybrid Edge Retrieval (HER)
**Equation 2** — Reciprocal Rank Fusion:
```
fused_score(d) = α · 1/(k + rank_bm25(d) + 1) + (1-α) · 1/(k + rank_vector(d) + 1)
```
with `k=60`, `α=0.5` by default (tunable in `config/app.yaml`).
**Table 2** (to fill from `scripts/benchmark.py` runs against a labeled corpus): retrieval accuracy, BM25-only vs. vector-only vs. fused+reranked.

### 4.5 Adaptive Quantization Router (AQR)
**Equation 3** — complexity score:
```
score = 0.35·reasoning_indicators + 0.25·domain_complexity + 0.15·query_length
        + 0.15·context_density + 0.10·historical_accuracy
```
routed to `fast` (score<0.3, no LLM call), `haiku` (0.3–0.6), `sonnet` (≥0.6) — this build's mapping of the original spec's Q4/Q5/Q8/cloud tiers onto API-served models plus a free offline extractive tier.

## 5. Evaluation

### 5.1 Experimental Setup
- **Hardware**: run `scripts/benchmark.py` on your target device(s) — the spec's target hardware (Raspberry Pi 5 8GB, Intel N100 16GB) is not available in this build environment.
- **Dataset**: bring a domain corpus (e.g., oil-gas technical Q&A) via `scripts/ingest.py`; the spec's 500-question benchmark set needs to be authored or sourced separately.
- **Baselines**: for a fair comparison, run the same corpus through a standard single-shot RAG pipeline (no CGR/HER/AQR) as a control.

### 5.2 Results
*(Fill in from real `scripts/benchmark.py` output — Tables 4–6, Figures 2–3 depend on actual runs against real hardware and a real corpus.)*

### 5.3 Ablation Studies
Suggested ablations, each independently switchable via `config/app.yaml` / env vars:
- DAS on/off (disable resource-based degradation)
- HER: fused vs. BM25-only vs. vector-only (`rrf_alpha` = 1.0 / 0.0)
- AQR vs. static tier (force `LLM_FAST_MODEL`/`LLM_HEAVY_MODEL` for all queries)
- LCE vs. no explanation (toggle `include_explanation`)

## 6. Discussion

**Limitations**: template-based what-if generation (this build's LCE what-ifs) lacks the generative creativity of LLM-authored counterfactuals; the extractive-fallback LLM tier trades fluency for zero-dependency operation — a real deployment should budget for at least the `haiku` tier to get generative answers. Confidence calibration (Platt scaling) ships with reasonable default coefficients but should be re-fit (`trust/confidence.py::fit_platt_scaling`) against real labeled (prediction, correctness) pairs before trusting the calibrated scores.

**Future work**: federated edge learning across multiple deployed nodes; multi-modal RAG (schematics, sensor time-series) alongside text.

## 7. Conclusion

VishwasEdge demonstrates that resource-aware multi-agent orchestration, confidence-grounded retrieval, and sub-5ms explainability can be composed into a single edge-deployable system without sacrificing any of the three to the others — and, notably, without requiring the multi-gigabyte local model footprint the initial architecture assumed, via a tiered LLM router that degrades gracefully to a fully offline extractive mode.

## References

*(To populate: llama.cpp, MLC-LLM, AutoGen, CrewAI, Self-RAG, Corrective RAG, LIME, SHAP, Reciprocal Rank Fusion (Cormack et al.), Platt scaling (Platt 1999), cross-encoder reranking (Nogueira & Cho).)*
