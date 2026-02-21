"""Smoke tests — Memory Manager"""
import os
import pytest

BASE = os.getenv("MEMORY_MANAGER_URL", "http://localhost:8001")


@pytest.mark.smoke
class TestMemoryManagerHealth:
    def test_health_status(self, http):
        r = http.get(f"{BASE}/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["agent"] == "memory-manager"

    def test_metrics_endpoint(self, http):
        r = http.get(f"{BASE}/metrics")
        assert r.status_code == 200
        assert "bodhi_memory_stored_total" in r.text
        assert "bodhi_memory_retrieved_total" in r.text


@pytest.mark.smoke
class TestMemoryManagerStore:
    def test_store_episodic(self, http):
        r = http.post(f"{BASE}/store", json={
            "content": "smoke test episodic memory",
            "memory_type": "episodic",
            "importance": 0.5,
            "session_id": "smoke-test",
            "metadata": {"source": "smoke"},
        })
        assert r.status_code == 200
        body = r.json()
        assert "id" in body          # StoreResponse returns {id, memory_type}
        assert body.get("memory_type") == "episodic"

    def test_store_working(self, http):
        r = http.post(f"{BASE}/store", json={
            "content": "smoke test working memory",
            "memory_type": "working",
            "importance": 0.3,
            "session_id": "smoke-test",
            "metadata": {},
        })
        assert r.status_code == 200

    def test_store_semantic(self, http):
        r = http.post(f"{BASE}/store", json={
            "content": "the user prefers dark mode",
            "memory_type": "semantic",
            "importance": 0.8,
            "session_id": "smoke-test",
            "metadata": {"category": "preference"},
        }, timeout=30)
        assert r.status_code == 200

    def test_store_invalid_type_rejected(self, http):
        r = http.post(f"{BASE}/store", json={
            "content": "bad type",
            "memory_type": "invalid",
            "importance": 0.5,
            "session_id": "smoke-test",
        })
        assert r.status_code == 422


@pytest.mark.smoke
class TestMemoryManagerRetrieve:
    def test_retrieve_returns_list(self, http):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "dark mode preference",
            "limit": 5,
            "min_score": 0.0,
        }, timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)   # /retrieve returns list[MemoryResult]

    def test_recent_returns_list(self, http):
        r = http.get(f"{BASE}/recent?limit=5&session_id=smoke-test")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)   # /recent returns list[dict]

    def test_recent_contains_stored_memory(self, http):
        r = http.get(f"{BASE}/recent?limit=10&session_id=smoke-test")
        contents = [m["content"] for m in r.json()]
        assert any("smoke test" in c for c in contents)
