"""Prometheus metrics: counters, histograms, gauges."""

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

registry = CollectorRegistry()

QUERY_COUNT = Counter(
    "vishwasedge_queries_total", "Total queries processed", ["tier", "status"], registry=registry
)
QUERY_LATENCY = Histogram(
    "vishwasedge_query_latency_ms",
    "End-to-end query latency in milliseconds",
    buckets=(10, 25, 50, 80, 100, 150, 200, 300, 500, 1000, 2000),
    registry=registry,
)
RETRIEVAL_LATENCY = Histogram(
    "vishwasedge_retrieval_latency_ms",
    "Retrieval latency in milliseconds",
    buckets=(5, 10, 20, 40, 80, 150, 300),
    registry=registry,
)
EXPLANATION_LATENCY = Histogram(
    "vishwasedge_explanation_latency_ms",
    "Explanation generation latency in milliseconds",
    buckets=(1, 2, 5, 10, 25, 50),
    registry=registry,
)
ACTIVE_QUERIES = Gauge("vishwasedge_active_queries", "In-flight queries", registry=registry)
RESOURCE_CPU_PERCENT = Gauge("vishwasedge_cpu_percent", "CPU utilization percent", registry=registry)
RESOURCE_MEMORY_MB = Gauge("vishwasedge_memory_mb", "Process memory usage in MB", registry=registry)
DEGRADATION_COUNT = Counter(
    "vishwasedge_degradations_total", "DAS degradation events", ["strategy"], registry=registry
)


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(registry), CONTENT_TYPE_LATEST
