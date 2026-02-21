from prometheus_client import Counter, Histogram

language_requests_total = Counter(
    "bodhi_language_requests_total",
    "Total requests per endpoint",
    ["endpoint"],
)

language_latency_seconds = Histogram(
    "bodhi_language_latency_seconds",
    "Request latency per endpoint",
    ["endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

intent_classified_total = Counter(
    "bodhi_intent_classified_total",
    "Total intents classified by label",
    ["intent"],
)
