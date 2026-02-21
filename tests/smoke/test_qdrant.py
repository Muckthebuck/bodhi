"""Smoke tests — Qdrant vector store"""
import pytest


@pytest.mark.smoke
class TestQdrant:
    BASE = "http://localhost:6333"

    def test_healthz(self, http):
        r = http.get(f"{self.BASE}/healthz")
        assert r.status_code == 200

    def test_readyz(self, http):
        r = http.get(f"{self.BASE}/readyz")
        assert r.status_code == 200

    def test_collections_endpoint(self, http):
        r = http.get(f"{self.BASE}/collections")
        assert r.status_code == 200
        assert "result" in r.json()

    def test_telemetry_endpoint(self, http):
        r = http.get(f"{self.BASE}/telemetry")
        assert r.status_code == 200
