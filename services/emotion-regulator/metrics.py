from prometheus_client import Counter, Gauge

emotion_updates_total = Counter(
    "bodhi_emotion_updates_total",
    "Total number of emotion update events processed",
    ["event_type"],
)

emotion_state = Gauge(
    "bodhi_emotion_state",
    "Current VAD dimension value",
    ["dimension"],
)

emotion_transitions_total = Counter(
    "bodhi_emotion_transitions_total",
    "Total number of emotion transition ticks that caused a meaningful state change",
)
