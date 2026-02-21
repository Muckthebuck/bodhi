from prometheus_client import Counter, Histogram

memory_stored_total = Counter(
    "bodhi_memory_stored_total",
    "Total number of memories stored",
    ["memory_type"],
)

memory_retrieved_total = Counter(
    "bodhi_memory_retrieved_total",
    "Total number of memory retrieval requests",
)

consolidation_runs_total = Counter(
    "bodhi_consolidation_runs_total",
    "Total number of consolidation runs completed",
)

memory_latency_seconds = Histogram(
    "bodhi_memory_latency_seconds",
    "Latency of memory operations in seconds",
    ["operation"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
