"""
Semantic reasoning tests — emotion-regulator

Tests sequential event accumulation, transition direction consistency,
overflow clamping under adversarial inputs, and drift-toward-baseline logic.
"""
import sys
import pytest

_main = sys.modules["er_main"]

_clamp = _main._clamp
_vad_clamp = _main._vad_clamp
_derive_label = _main._derive_label
_max_delta = _main._max_delta
EVENT_EFFECTS = _main.EVENT_EFFECTS
BASELINE = _main.BASELINE
EMOTION_TRANSITION_SPEED = _main.EMOTION_TRANSITION_SPEED
DRIFT_RATE = _main.DRIFT_RATE


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _apply_event_to_state(
    vad: dict[str, float], event_type: str, intensity: float = 1.0
) -> dict[str, float]:
    """Pure simulation of _apply_event without async/Redis."""
    effects = EVENT_EFFECTS.get(event_type, {})
    result = dict(vad)
    for dim, delta in effects.items():
        result[dim] = _vad_clamp(dim, result[dim] + delta * intensity)
    return result


def _apply_events(events: list[str], intensity: float = 1.0) -> dict[str, float]:
    """Apply a sequence of events starting from baseline."""
    state = dict(BASELINE)
    for event in events:
        state = _apply_event_to_state(state, event, intensity)
    return state


def _tick(current: dict, target: dict, steps: int = 1) -> tuple[dict, dict]:
    """Simulate N transition ticks (1 second each)."""
    c = dict(current)
    t = dict(target)
    for _ in range(steps):
        for dim in ("valence", "arousal", "dominance"):
            step = EMOTION_TRANSITION_SPEED
            diff = t[dim] - c[dim]
            if abs(diff) <= step:
                c[dim] = t[dim]
            else:
                c[dim] += step * (1 if diff > 0 else -1)

            drift_diff = BASELINE[dim] - t[dim]
            drift_step = DRIFT_RATE
            if abs(drift_diff) <= drift_step:
                t[dim] = BASELINE[dim]
            else:
                t[dim] += drift_step * (1 if drift_diff > 0 else -1)

            c[dim] = _vad_clamp(dim, c[dim])
            t[dim] = _vad_clamp(dim, t[dim])
    return c, t


# ─────────────────────────────────────────────────────────────────────────────
# Sequential event accumulation
# ─────────────────────────────────────────────────────────────────────────────

class TestEventAccumulation:
    """Multiple positive events should push state further than one event."""

    def test_repeated_positive_feedback_accumulates(self):
        one = _apply_events(["user.positive_feedback"])
        three = _apply_events(["user.positive_feedback"] * 3)
        assert three["valence"] >= one["valence"]

    def test_positive_then_negative_partially_cancels(self):
        positive = _apply_events(["user.positive_feedback"])
        cancelled = _apply_events(["user.positive_feedback", "user.negative_feedback"])
        assert cancelled["valence"] < positive["valence"]

    def test_greeting_increases_valence_from_baseline(self):
        after = _apply_events(["user.greeting"])
        assert after["valence"] > BASELINE["valence"]

    def test_farewell_decreases_arousal(self):
        after = _apply_events(["user.farewell"])
        assert after["arousal"] < BASELINE["arousal"] + EVENT_EFFECTS["user.farewell"]["arousal"] + 0.01

    def test_task_completed_increases_dominance(self):
        after = _apply_events(["task.completed"])
        assert after["dominance"] > BASELINE["dominance"]

    def test_task_failed_decreases_dominance(self):
        after = _apply_events(["task.failed"])
        assert after["dominance"] < BASELINE["dominance"]

    def test_order_matters_positive_first(self):
        pos_then_neg = _apply_events(["user.positive_feedback", "user.negative_feedback"])
        neg_then_pos = _apply_events(["user.negative_feedback", "user.positive_feedback"])
        # Both sequences reach the same final state because effects are additive
        # (order only matters if clamping occurs at intermediate steps)
        for dim in ("valence", "arousal", "dominance"):
            assert abs(pos_then_neg[dim] - neg_then_pos[dim]) < 0.01

    def test_many_task_completions_clamp_at_ceiling(self):
        after = _apply_events(["task.completed"] * 50)
        assert after["dominance"] <= 1.0
        assert after["valence"] <= 1.0

    def test_many_failures_clamp_at_floor(self):
        after = _apply_events(["task.failed"] * 50)
        assert after["dominance"] >= 0.0
        assert after["valence"] >= -1.0


# ─────────────────────────────────────────────────────────────────────────────
# Transition direction consistency
# ─────────────────────────────────────────────────────────────────────────────

class TestTransitionDirectionConsistency:
    """The current state must always move monotonically toward the target."""

    def test_current_moves_toward_higher_target(self):
        current = {"valence": 0.0, "arousal": 0.3, "dominance": 0.5}
        target = {"valence": 0.8, "arousal": 0.3, "dominance": 0.5}
        c1, _ = _tick(current, target, steps=1)
        assert c1["valence"] > current["valence"]

    def test_current_moves_toward_lower_target(self):
        current = {"valence": 0.8, "arousal": 0.3, "dominance": 0.5}
        target = {"valence": 0.1, "arousal": 0.3, "dominance": 0.5}
        c1, _ = _tick(current, target, steps=1)
        assert c1["valence"] < current["valence"]

    def test_transition_is_monotonic_over_many_steps(self):
        # Test monotonicity for the first 8 steps only; after ~10 steps the drift
        # toward baseline can pull target below current, reversing direction.
        current = {"valence": -0.5, "arousal": 0.1, "dominance": 0.2}
        target = {"valence": 0.7, "arousal": 0.8, "dominance": 0.9}
        prev_valence = current["valence"]
        for _ in range(8):
            current, target = _tick(current, target, steps=1)
            assert current["valence"] >= prev_valence - 1e-9  # monotonically increasing
            prev_valence = current["valence"]

    def test_overshooting_does_not_occur(self):
        current = {"valence": 0.0, "arousal": 0.3, "dominance": 0.5}
        target = {"valence": 0.2, "arousal": 0.3, "dominance": 0.5}
        for _ in range(100):
            current, target = _tick(current, target, steps=1)
        # After many ticks, current should settle near target, not overshoot
        assert current["valence"] <= target["valence"] + 0.01

    def test_already_at_target_stays_stable(self):
        state = dict(BASELINE)
        target = dict(BASELINE)
        c1, t1 = _tick(state, target, steps=10)
        for dim in ("valence", "arousal", "dominance"):
            assert abs(c1[dim] - BASELINE[dim]) < 0.05


# ─────────────────────────────────────────────────────────────────────────────
# Drift toward baseline
# ─────────────────────────────────────────────────────────────────────────────

class TestDriftTowardBaseline:
    """Without new events, the target should slowly drift back to baseline."""

    def test_elevated_target_drifts_down(self):
        current = {"valence": 0.9, "arousal": 0.9, "dominance": 0.9}
        target = {"valence": 0.9, "arousal": 0.9, "dominance": 0.9}
        _, t_after = _tick(current, target, steps=10)
        assert t_after["valence"] < target["valence"]

    def test_depressed_target_drifts_up_toward_baseline(self):
        current = {"valence": -0.8, "arousal": 0.1, "dominance": 0.1}
        target = {"valence": -0.8, "arousal": 0.1, "dominance": 0.1}
        _, t_after = _tick(current, target, steps=10)
        assert t_after["valence"] > target["valence"]

    def test_drift_reaches_baseline_eventually(self):
        current = {"valence": 0.9, "arousal": 0.9, "dominance": 0.9}
        target = {"valence": 0.9, "arousal": 0.9, "dominance": 0.9}
        # With DRIFT_RATE=0.02/s and distance ~0.8, needs ~40 ticks
        for _ in range(100):
            current, target = _tick(current, target, steps=1)
        for dim in ("valence", "arousal", "dominance"):
            assert abs(target[dim] - BASELINE[dim]) < 0.05, \
                f"{dim}: target={target[dim]:.3f}, baseline={BASELINE[dim]:.3f}"


# ─────────────────────────────────────────────────────────────────────────────
# Emotion label reasoning
# Labels should follow logically from VAD state
# ─────────────────────────────────────────────────────────────────────────────

class TestEmotionLabelReasoning:
    """Verify the label derivation logic is self-consistent."""

    def test_positive_events_eventually_produce_positive_label(self):
        state = _apply_events(["user.positive_feedback"] * 5)
        label = _derive_label(state["valence"], state["arousal"], state["dominance"], 0.8)
        assert label in ("excited", "happy", "content"), \
            f"Expected positive label, got '{label}' for state {state}"

    def test_failure_events_produce_negative_label(self):
        state = _apply_events(["task.failed"] * 5)
        label = _derive_label(state["valence"], state["arousal"], state["dominance"], 0.5)
        assert label in ("sad", "anxious", "frustrated"), \
            f"Expected negative label, got '{label}' for state {state}"

    def test_label_is_string(self):
        for v in [-0.8, -0.3, 0.0, 0.3, 0.8]:
            for a in [0.2, 0.6]:
                label = _derive_label(v, a, 0.5, 0.7)
                assert isinstance(label, str)
                assert len(label) > 0

    def test_baseline_state_produces_calm_or_curious(self):
        label = _derive_label(
            BASELINE["valence"], BASELINE["arousal"], BASELINE["dominance"], 0.8
        )
        assert label in ("calm", "curious", "content"), \
            f"Baseline should be calm/curious/content, got '{label}'"

    @pytest.mark.parametrize("openness,expected", [
        (0.9, "curious"),
        (0.5, "calm"),
    ])
    def test_openness_determines_calm_vs_curious(self, openness, expected):
        # At neutral VAD, openness tips the label
        label = _derive_label(0.1, 0.3, 0.5, openness)
        assert label == expected


# ─────────────────────────────────────────────────────────────────────────────
# Intensity scaling
# ─────────────────────────────────────────────────────────────────────────────

class TestIntensityScaling:
    """Higher intensity should produce larger state changes."""

    def test_full_intensity_larger_delta_than_half(self):
        baseline = dict(BASELINE)
        full = _apply_event_to_state(baseline, "user.positive_feedback", intensity=1.0)
        half = _apply_event_to_state(baseline, "user.positive_feedback", intensity=0.5)
        assert full["valence"] > half["valence"]

    def test_zero_intensity_is_no_op(self):
        baseline = dict(BASELINE)
        after = _apply_event_to_state(baseline, "user.positive_feedback", intensity=0.0)
        for dim in ("valence", "arousal", "dominance"):
            assert abs(after[dim] - baseline[dim]) < 1e-9

    def test_high_intensity_still_clamped(self):
        baseline = dict(BASELINE)
        after = _apply_event_to_state(baseline, "user.positive_feedback", intensity=100.0)
        assert after["valence"] <= 1.0
        assert after["arousal"] <= 1.0
        assert after["dominance"] <= 1.0
