"""Unit tests — emotion-regulator pure logic (no I/O)"""

import sys

import pytest

# Modules pre-loaded once by tests/unit/conftest.py to avoid Prometheus re-registration
_main = sys.modules["er_main"]

_clamp = _main._clamp
_vad_clamp = _main._vad_clamp
_derive_label = _main._derive_label
_max_delta = _main._max_delta
EVENT_EFFECTS = _main.EVENT_EFFECTS
DEFAULT_PERSONALITY = _main.DEFAULT_PERSONALITY
BASELINE = _main.BASELINE


class TestClamp:
    def test_clamp_within_range(self):
        assert _clamp(0.5, 0.0, 1.0) == 0.5

    def test_clamp_below_min(self):
        assert _clamp(-2.0, -1.0, 1.0) == -1.0

    def test_clamp_above_max(self):
        assert _clamp(1.5, 0.0, 1.0) == 1.0

    def test_clamp_at_boundary(self):
        assert _clamp(1.0, 0.0, 1.0) == 1.0
        assert _clamp(0.0, 0.0, 1.0) == 0.0


class TestVadClamp:
    def test_valence_allows_negative(self):
        assert _vad_clamp("valence", -0.5) == -0.5

    def test_valence_clamps_below_minus_one(self):
        assert _vad_clamp("valence", -1.5) == -1.0

    def test_valence_clamps_above_one(self):
        assert _vad_clamp("valence", 1.5) == 1.0

    def test_arousal_clamps_below_zero(self):
        assert _vad_clamp("arousal", -0.5) == 0.0

    def test_dominance_clamps_below_zero(self):
        assert _vad_clamp("dominance", -0.1) == 0.0

    def test_arousal_clamps_above_one(self):
        assert _vad_clamp("arousal", 1.5) == 1.0


class TestDeriveLabel:
    def test_excited_high_valence_high_arousal(self):
        assert _derive_label(0.5, 0.7, 0.5, 0.8) == "excited"

    def test_happy_high_valence_low_arousal(self):
        assert _derive_label(0.7, 0.3, 0.5, 0.8) == "happy"

    def test_content_moderate_valence_low_arousal(self):
        assert _derive_label(0.4, 0.3, 0.5, 0.8) == "content"

    def test_anxious_negative_valence_high_arousal_low_dominance(self):
        assert _derive_label(-0.5, 0.7, 0.2, 0.5) == "anxious"

    def test_frustrated_negative_valence_high_arousal_high_dominance(self):
        assert _derive_label(-0.5, 0.7, 0.7, 0.5) == "frustrated"

    def test_sad_negative_valence_low_arousal(self):
        assert _derive_label(-0.5, 0.3, 0.5, 0.8) == "sad"

    def test_curious_neutral_high_openness(self):
        assert _derive_label(0.1, 0.3, 0.5, 0.8) == "curious"

    def test_calm_neutral_low_openness(self):
        assert _derive_label(0.1, 0.3, 0.5, 0.5) == "calm"


class TestMaxDelta:
    def test_zero_delta(self):
        a = {"valence": 0.5, "arousal": 0.5, "dominance": 0.5}
        assert _max_delta(a, a) == 0.0

    def test_picks_largest_delta(self):
        a = {"valence": 0.5, "arousal": 0.5, "dominance": 0.5}
        b = {"valence": 0.6, "arousal": 0.5, "dominance": 0.9}
        assert _max_delta(a, b) == pytest.approx(0.4)


class TestEventEffects:
    def test_all_events_defined(self):
        expected = {
            "user.positive_feedback",
            "user.negative_feedback",
            "user.greeting",
            "user.farewell",
            "task.completed",
            "task.failed",
            "user.input",
            "language.response",
        }
        assert set(EVENT_EFFECTS.keys()) == expected

    def test_positive_feedback_increases_valence(self):
        assert EVENT_EFFECTS["user.positive_feedback"]["valence"] > 0

    def test_negative_feedback_decreases_valence(self):
        assert EVENT_EFFECTS["user.negative_feedback"]["valence"] < 0

    def test_task_completed_increases_dominance(self):
        assert EVENT_EFFECTS["task.completed"]["dominance"] > 0

    def test_all_effects_have_vad_keys(self):
        for event, effects in EVENT_EFFECTS.items():
            assert set(effects.keys()) == {"valence", "arousal", "dominance"}, event

    def test_all_deltas_within_reasonable_range(self):
        for event, effects in EVENT_EFFECTS.items():
            for dim, delta in effects.items():
                assert -1.0 <= delta <= 1.0, f"{event}.{dim} delta {delta} out of range"


class TestDefaultPersonality:
    def test_has_all_big_five_traits(self):
        expected = {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}
        assert set(DEFAULT_PERSONALITY.keys()) == expected

    def test_all_values_in_range(self):
        for trait, val in DEFAULT_PERSONALITY.items():
            assert 0.0 <= val <= 1.0, f"{trait}={val}"

    def test_bodhi_is_open_and_agreeable(self):
        assert DEFAULT_PERSONALITY["openness"] >= 0.7
        assert DEFAULT_PERSONALITY["agreeableness"] >= 0.7

    def test_bodhi_is_emotionally_stable(self):
        assert DEFAULT_PERSONALITY["neuroticism"] <= 0.3


class TestBaseline:
    def test_baseline_has_all_dimensions(self):
        assert set(BASELINE.keys()) == {"valence", "arousal", "dominance"}

    def test_baseline_valence_in_range(self):
        assert -1.0 <= BASELINE["valence"] <= 1.0

    def test_baseline_arousal_dominance_in_range(self):
        assert 0.0 <= BASELINE["arousal"] <= 1.0
        assert 0.0 <= BASELINE["dominance"] <= 1.0
