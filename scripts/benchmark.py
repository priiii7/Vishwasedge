"""Full system benchmark suite — measures the metrics used in the paper's
evaluation section (§Phase 8) by calling the orchestrator directly, so it
doesn't need a running HTTP server.

Usage:
    python scripts/benchmark.py --queries 20
"""

import argparse
import asyncio
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.agents.orchestrator import QueryOptions, handle_query  # noqa: E402
from backend.trust.explainer import explain  # noqa: E402

SAMPLE_QUERIES = [
    "What is the safe operating pressure for well W-123?",
    "Why does wellhead pressure fluctuate during startup?",
    "How do I perform an emergency shutdown on a flowline valve?",
    "Compare the corrosion resistance of carbon steel vs duplex stainless casing.",
    "What are the safety thresholds for compressor vibration?",
]

TARGETS = {
    "end_to_end_latency_ms": {"target": 150, "unit": "ms"},
    "retrieval_latency_ms": {"target": 80, "unit": "ms"},
    "explanation_latency_ms": {"target": 5, "unit": "ms"},
}


async def run(num_queries: int) -> None:
    e2e_latencies: list[float] = []
    retrieval_latencies: list[float] = []
    explanation_latencies: list[float] = []
    confidences: list[float] = []

    for i in range(num_queries):
        query = SAMPLE_QUERIES[i % len(SAMPLE_QUERIES)]
        start = time.perf_counter()
        result = await handle_query(query, None, QueryOptions(include_explanation=True, max_docs=5))
        e2e_latencies.append((time.perf_counter() - start) * 1000)
        retrieval_latencies.append(result.retrieval.latency_ms)
        confidences.append(result.confidence)
        if result.explanation:
            explanation_latencies.append(result.explanation["explanation_latency_ms"])

    def _summ(values: list[float]) -> dict:
        if not values:
            return {"p50": 0, "p95": 0, "mean": 0}
        sorted_v = sorted(values)
        return {
            "p50": round(sorted_v[len(sorted_v) // 2], 3),
            "p95": round(sorted_v[int(len(sorted_v) * 0.95) - 1], 3),
            "mean": round(statistics.mean(values), 3),
        }

    print("=== VishwasEdge Benchmark ===")
    print(f"Queries run: {num_queries}")
    print(f"End-to-end latency (ms): {_summ(e2e_latencies)} — target p95 < {TARGETS['end_to_end_latency_ms']['target']}")
    print(f"Retrieval latency (ms):  {_summ(retrieval_latencies)} — target < {TARGETS['retrieval_latency_ms']['target']}")
    print(f"Explanation latency (ms): {_summ(explanation_latencies)} — target < {TARGETS['explanation_latency_ms']['target']}")
    print(f"Mean confidence: {round(statistics.mean(confidences), 3) if confidences else 0}")
    print(
        "\nNote: with no ANTHROPIC_API_KEY configured, answers come from the offline "
        "extractive tier — latency numbers will look better than the cloud tiers and "
        "should be re-run with an API key + real domain corpus for paper-grade results."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", type=int, default=20)
    args = parser.parse_args()
    asyncio.run(run(args.queries))


if __name__ == "__main__":
    main()
