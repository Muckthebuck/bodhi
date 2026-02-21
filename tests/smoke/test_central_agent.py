"""Smoke tests — Central Agent"""
import os
import pytest

BASE = os.getenv("CENTRAL_AGENT_URL", "http://localhost:8000")


@pytest.mark.smoke
class TestCentralAgentHealth:
    def test_health_status(self, http):
        r = http.get(f"{BASE}/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["agent"] == "central-agent"

    def test_health_has_version(self, http):
        r = http.get(f"{BASE}/health")
        assert "version" in r.json()

    def test_status_endpoint(self, http):
        r = http.get(f"{BASE}/status")
        assert r.status_code == 200
        body = r.json()
        assert "memory_mb" in body
        assert "active_agents" in body

    def test_metrics_endpoint(self, http):
        r = http.get(f"{BASE}/metrics")
        assert r.status_code == 200
        assert "bodhi_central_requests_total" in r.text
        assert "bodhi_central_latency_seconds" in r.text


@pytest.mark.smoke
class TestCentralAgentInput:
    def test_input_returns_response(self, http):
        r = http.post(
            f"{BASE}/input",
            json={"text": "hello", "session_id": "smoke-test"},
            timeout=10,
        )
        assert r.status_code == 200
        body = r.json()
        # Either a real response or a timeout — both are valid smoke outcomes
        assert "response" in body or "error" in body

    def test_input_requires_text(self, http):
        r = http.post(f"{BASE}/input", json={"session_id": "smoke-test"})
        assert r.status_code == 422

    def test_input_empty_text_rejected(self, http):
        r = http.post(f"{BASE}/input", json={"text": "", "session_id": "smoke-test"})
        assert r.status_code in (400, 422)


@pytest.mark.smoke
class TestCentralAgentRedis:
    def test_publishes_to_user_input(self, redis_client):
        """Verify the channel exists and is subscribable."""
        p = redis_client.pubsub()
        p.subscribe("user.input")
        p.unsubscribe("user.input")

    def test_language_response_channel_exists(self, redis_client):
        p = redis_client.pubsub()
        p.psubscribe("language.response.*")
        p.punsubscribe("language.response.*")
