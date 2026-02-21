from prometheus_client import Counter, Gauge, Histogram

requests_total = Counter(
    "bodhi_central_requests_total",
    "Total requests processed by central-agent",
    ["status"],
)

latency_seconds = Histogram(
    "bodhi_central_latency_seconds",
    "Request latency for central-agent",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

active_agents = Gauge(
    "bodhi_active_agents",
    "Number of active sub-agents visible to central-agent",
)
