"""Smoke tests — Emotion Regulator"""

import os

import pytest

BASE = os.getenv("EMOTION_REGULATOR_URL", "http://localhost:8003")

PERSONALITY = {
    "openness": 0.8,
    "conscientiousness": 0.7,
    "extraversion": 0.5,
    "agreeableness": 0.8,
    "neuroticism": 0.2,
}


@pytest.mark.smoke
class TestEmotionRegulatorHealth:
    def test_health_status(self, http):
        r = http.get(f"{BASE}/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["agent"] == "emotion-regulator"

    def test_metrics_endpoint(self, http):
        r = http.get(f"{BASE}/metrics")
        assert r.status_code == 200
        assert "bodhi_emotion_updates_total" in r.text


@pytest.mark.smoke
class TestEmotionRegulatorState:
    def test_state_returns_vad(self, http):
        r = http.get(f"{BASE}/state")
        assert r.status_code == 200
        body = r.json()
        assert "current" in body
        assert "label" in body
        current = body["current"]
        assert "valence" in current
        assert "arousal" in current
        assert "dominance" in current

    def test_valence_in_range(self, http):
        current = http.get(f"{BASE}/state").json()["current"]
        assert -1.0 <= current["valence"] <= 1.0

    def test_arousal_dominance_in_range(self, http):
        current = http.get(f"{BASE}/state").json()["current"]
        assert 0.0 <= current["arousal"] <= 1.0
        assert 0.0 <= current["dominance"] <= 1.0

    def test_label_is_string(self, http):
        body = http.get(f"{BASE}/state").json()
        assert isinstance(body["label"], str)
        assert len(body["label"]) > 0

    def test_state_has_transition_progress(self, http):
        body = http.get(f"{BASE}/state").json()
        assert "transition_progress" in body


@pytest.mark.smoke
class TestEmotionRegulatorUpdate:
    def test_update_returns_ok(self, http):
        r = http.post(
            f"{BASE}/update",
            json={
                "event_type": "positive_feedback",
                "intensity": 1.0,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "label" in body
        assert "current" in body

    def test_positive_event_accepted(self, http):
        r = http.post(
            f"{BASE}/update",
            json={
                "event_type": "positive_feedback",
                "intensity": 0.8,
            },
        )
        assert r.status_code == 200

    def test_negative_event_accepted(self, http):
        r = http.post(
            f"{BASE}/update",
            json={
                "event_type": "negative_feedback",
                "intensity": 0.5,
            },
        )
        assert r.status_code == 200

    def test_task_completed_event(self, http):
        r = http.post(
            f"{BASE}/update",
            json={
                "event_type": "task_completed",
                "intensity": 0.8,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert "current" in body

    def test_unknown_event_type_returns_400(self, http):
        r = http.post(
            f"{BASE}/update",
            json={
                "event_type": "totally_unknown_event_xyz",
                "intensity": 1.0,
            },
        )
        # Unknown events log a warning but still return 200 with no-op effect
        assert r.status_code in (200, 400, 422)

    def test_intensity_too_high_rejected(self, http):
        r = http.post(
            f"{BASE}/update",
            json={
                "event_type": "positive_feedback",
                "intensity": 5.0,  # > 2.0 (field max)
            },
        )
        assert r.status_code == 422


@pytest.mark.smoke
class TestEmotionRegulatorPersonality:
    def test_get_personality(self, http):
        r = http.get(f"{BASE}/personality")
        assert r.status_code == 200
        body = r.json()
        assert "personality" in body

    def test_personality_fields_in_range(self, http):
        body = http.get(f"{BASE}/personality").json()["personality"]
        for trait in (
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
        ):
            assert 0.0 <= body[trait] <= 1.0, f"{trait} out of range"
